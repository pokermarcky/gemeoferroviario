"""Converte o desenho SVG do elevado em imagem PNG para os arquivos baixados.

Usa só o Pillow (já instalado com o reportlab e o Streamlit) e as fontes Vera que
acompanham o reportlab, sem depender de bibliotecas de sistema como o Cairo.
Entende apenas o subconjunto de SVG que `elevated_drawing` produz (retângulos,
linhas, polígonos, caminhos simples, círculos, textos, padrões e degradê). As cores
vêm do próprio SVG, então qualquer mudança de cor no desenho chega ao arquivo.
"""
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import math
import re
from xml.etree import ElementTree as ET

import reportlab
from PIL import Image, ImageDraw, ImageFont, ImageColor

from railbudget.elevated_drawing import elevated_svg, drawing_parameters

FONTS=Path(reportlab.__file__).parent/'fonts'
SUPERSAMPLE=2
# A Vera é mais larga que a fonte da tela; reduz um pouco para os textos caberem no mesmo lugar.
FONT_FACTOR=0.88


def _tag(element):
    return element.tag.split('}')[-1]


def _color(value,default=None):
    if not value or value=='none':return default
    try:return ImageColor.getrgb(value)
    except ValueError:return default


def _font(size,bold):
    return ImageFont.truetype(str(FONTS/('VeraBd.ttf' if bold else 'Vera.ttf')),max(int(round(size)),1))


def _floats(text):
    return [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?',text or '')]


def _path_points(d):
    """Pontos de um caminho com comandos M, L, H, V (absolutos ou relativos) e Z."""
    points=[];x=y=0.
    for command,args in re.findall(r'([MLHVZmlhvz])([^MLHVZmlhvz]*)',d):
        nums=_floats(args)
        if command in 'Mm' or command in 'Ll':
            for i in range(0,len(nums)-1,2):
                if command.islower():x+=nums[i];y+=nums[i+1]
                else:x,y=nums[i],nums[i+1]
                points.append((x,y))
        elif command in 'Hh':
            for value in nums:
                x=x+value if command=='h' else value;points.append((x,y))
        elif command in 'Vv':
            for value in nums:
                y=y+value if command=='v' else value;points.append((x,y))
    return points


class _Canvas:
    def __init__(self,svg,scale):
        self.root=ET.fromstring(svg)
        _,_,width,height=_floats(self.root.get('viewBox'))
        self.k=scale*SUPERSAMPLE
        style=self.root.get('style','')
        found=re.search(r'background:\s*(#[0-9a-fA-F]{3,6})',style)
        self.background=_color(found.group(1) if found else None,(255,255,255))
        found=re.search(r'border:\s*[\d.]+px\s+solid\s+(#[0-9a-fA-F]{3,6})',style)
        self.border=_color(found.group(1) if found else None)
        self.size=(int(width*self.k),int(height*self.k))
        self.image=Image.new('RGB',self.size,self.background)
        self.draw=ImageDraw.Draw(self.image)
        self.defs={el.get('id'):el for el in self.root.iter() if el.get('id')}
        self.textures={}

    def p(self,x,y):return (x*self.k,y*self.k)

    def _pattern_tile(self,el):
        """Ladrilho do padrão, desenhado uma vez por desenho."""
        ref=el.get('id')
        if ref not in self.textures:
            width=float(el.get('width'));height=float(el.get('height'))
            tile=Image.new('RGB',(max(int(width*self.k),1),max(int(height*self.k),1)),self.background)
            canvas=_Canvas.__new__(_Canvas)
            canvas.k=self.k;canvas.image=tile;canvas.draw=ImageDraw.Draw(tile);canvas.defs=self.defs
            canvas.background=self.background;canvas.textures={}
            for child in el:canvas.element(child)
            self.textures[ref]=tile
        return self.textures[ref]

    def _layer(self,el,size):
        """Camada do tamanho `size` preenchida pelo padrão (ladrilhado e girado) ou pelo degradê horizontal."""
        width,height=size
        if _tag(el)=='linearGradient':
            stops=[(float(s.get('offset')),_color(s.get('stop-color'),(200,200,200))) for s in el if _tag(s)=='stop']
            layer=Image.new('RGB',size);draw=ImageDraw.Draw(layer)
            for x in range(width):
                t=x/max(width-1,1)
                for (o1,c1),(o2,c2) in zip(stops,stops[1:]):
                    if o1<=t<=o2:
                        f=(t-o1)/(o2-o1) if o2>o1 else 0
                        draw.line([(x,0),(x,height)],fill=tuple(int(a+(b-a)*f) for a,b in zip(c1,c2)))
                        break
            return layer
        tile=self._pattern_tile(el)
        angle=_floats(el.get('patternTransform',''))
        side=int(math.hypot(width,height))+tile.size[0] if angle else None
        full=(side,side) if angle else (width,height)
        row=Image.new('RGB',(full[0],tile.size[1]))
        for x in range(0,full[0],tile.size[0]):row.paste(tile,(x,0))
        layer=Image.new('RGB',full)
        for y in range(0,full[1],tile.size[1]):layer.paste(row,(0,y))
        if not angle:return layer
        layer=layer.rotate(-angle[0],resample=Image.NEAREST)
        left=(side-width)//2;top=(side-height)//2
        return layer.crop((left,top,left+width,top+height))

    def _fill_shape(self,fill,shape):
        """Pinta a forma (função que desenha em um ImageDraw) com cor, padrão ou degradê."""
        found=re.match(r'url\(#([^)]+)\)',fill or '')
        if not found:
            color=_color(fill,(0,0,0) if fill is None else None)
            if color:shape(self.draw,color,None)
            return
        el=self.defs.get(found.group(1))
        if el is None:return
        mask=Image.new('L',self.image.size,0);shape(ImageDraw.Draw(mask),255,None)
        box=mask.getbbox()
        if not box:return
        layer=self._layer(el,(box[2]-box[0],box[3]-box[1]))
        self.image.paste(layer,box[:2],mask.crop(box))

    def _stroke(self,el):
        color=_color(el.get('stroke'))
        return (color,max(int(round(float(el.get('stroke-width',1))*self.k)),1)) if color else (None,0)

    def _dashed(self,a,b,color,width,dash):
        length=math.dist(a,b)
        if not length:return
        ux,uy=(b[0]-a[0])/length,(b[1]-a[1])/length
        pattern=[v*self.k for v in dash] or [length];pos=0.;i=0
        while pos<length:
            step=pattern[i%len(pattern)];end=min(pos+step,length)
            if i%2==0:
                self.draw.line([(a[0]+ux*pos,a[1]+uy*pos),(a[0]+ux*end,a[1]+uy*end)],fill=color,width=width)
            pos=end;i+=1

    def _arrow(self,tip,direction,color,width):
        ux,uy=direction;size=6*width/self.k*self.k
        # Ponta da seta como no marcador do SVG: centrada no ponto, apontando para fora.
        x,y=tip[0]+ux*size/2,tip[1]+uy*size/2
        base=(x-ux*size,y-uy*size)
        self.draw.polygon([(x,y),(base[0]-uy*size/2,base[1]+ux*size/2),(base[0]+uy*size/2,base[1]-ux*size/2)],fill=color)

    def element(self,el):
        tag=_tag(el)
        if tag in ('defs','title','marker','pattern','linearGradient'):return
        if tag=='rect':
            x,y=self.p(float(el.get('x',0)),float(el.get('y',0)))
            w=float(el.get('width',0))*self.k;h=float(el.get('height',0))*self.k
            if w<=0 or h<=0:return
            box=[x,y,x+w-1,y+h-1];radius=float(el.get('rx',0))*self.k
            def shape(draw,fill,outline,width=1):
                if radius:draw.rounded_rectangle(box,radius,fill=fill,outline=outline,width=width)
                else:draw.rectangle(box,fill=fill,outline=outline,width=width)
            self._fill_shape(el.get('fill'),shape)
            color,width=self._stroke(el)
            if color:shape(self.draw,None,color,width)
        elif tag in ('polygon','path'):
            if tag=='polygon':
                nums=_floats(el.get('points'));points=[self.p(nums[i],nums[i+1]) for i in range(0,len(nums)-1,2)]
            else:points=[self.p(x,y) for x,y in _path_points(el.get('d',''))]
            if len(points)<3:return
            self._fill_shape(el.get('fill'),lambda draw,fill,outline:draw.polygon(points,fill=fill))
            color,width=self._stroke(el)
            if color:self.draw.line(points+[points[0]],fill=color,width=width,joint='curve')
        elif tag=='circle':
            cx,cy=self.p(float(el.get('cx')),float(el.get('cy')));r=float(el.get('r'))*self.k
            self._fill_shape(el.get('fill'),lambda draw,fill,outline:draw.ellipse([cx-r,cy-r,cx+r,cy+r],fill=fill))
        elif tag=='line':
            a=self.p(float(el.get('x1')),float(el.get('y1')));b=self.p(float(el.get('x2')),float(el.get('y2')))
            color,width=self._stroke(el)
            if not color:return
            dash=_floats(el.get('stroke-dasharray'))
            if dash:self._dashed(a,b,color,width,dash)
            else:self.draw.line([a,b],fill=color,width=width)
            if el.get('marker-end') and math.dist(a,b):
                length=math.dist(a,b);ux,uy=(b[0]-a[0])/length,(b[1]-a[1])/length
                self._arrow(b,(ux,uy),color,width);self._arrow(a,(-ux,-uy),color,width)
        elif tag=='text':self._text(el)
        for child in el if tag=='svg' else ():self.element(child)

    def _text(self,el):
        value=el.text or ''
        if not value.strip():return
        size=float(el.get('font-size',12))*self.k*FONT_FACTOR
        font=_font(size,int(el.get('font-weight','400'))>=600)
        color=_color(el.get('fill'),(0,0,0))
        x,y=self.p(float(el.get('x',0)),float(el.get('y',0)))
        anchor={'start':'ls','middle':'ms','end':'rs'}[el.get('text-anchor','start')]
        rotation=_floats(el.get('transform',''))
        if not rotation:
            self.draw.text((x,y),value,font=font,fill=color,anchor=anchor);return
        # Texto girado (cotas verticais): desenha em camada própria e gira em torno do ponto.
        left,top,right,bottom=font.getbbox(value,anchor=anchor)
        layer=Image.new('L',(int(right-left)+4,int(bottom-top)+4),0)
        ImageDraw.Draw(layer).text((-left+2,-top+2),value,font=font,fill=255,anchor=anchor)
        turned=layer.rotate(-rotation[0],expand=True)
        # Após girar -90°, o ponto de ancoragem (x,y) fica à direita, no meio da altura.
        offset=(int(x-turned.size[0]+(bottom+2)),int(y-turned.size[1]/2))
        self.image.paste(Image.new('RGB',turned.size,color),offset,turned)

    def render(self):
        for child in self.root:self.element(child)
        if self.border:
            self.draw.rounded_rectangle([0,0,self.size[0]-1,self.size[1]-1],12*self.k,outline=self.border,width=self.k)
        return self.image.resize((self.size[0]//SUPERSAMPLE,self.size[1]//SUPERSAMPLE),Image.LANCZOS)


@lru_cache(maxsize=16)
def svg_to_png(svg,scale=2):
    """PNG do SVG em `scale` pixels por unidade do desenho."""
    out=BytesIO();_Canvas(svg,scale).render().save(out,'PNG',optimize=True)
    return out.getvalue()


def elevated_drawing_png(result,scale=2):
    """PNG do desenho do elevado para o resultado calculado, ou None se não houver elevado."""
    if not result.get('elevated'):return None
    return svg_to_png(elevated_svg(drawing_parameters(result['scenario'],result['elevated'])),scale)
