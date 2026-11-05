"""Desenho esquemático (SVG) do elevado: corte transversal e elevação longitudinal.

Só desenha; não calcula custo. As cotas exibidas são os valores do cenário,
e o traço é esquemático (sem escala) para caber na tela em qualquer combinação.
"""
from html import escape
import math

# Cores do tema: via permanente em destaque, estrutura em tons neutros.
RAIL='#b8322a';GUARD_RAIL='#7a1f1a';SLEEPER='#a0614c';BALLAST='#c9ad80';CURB='#9c8466'
CONCRETE='#d9cdc6';CONCRETE_DARK='#b9a79e';STEEL='#6f6a73';SOIL='#e8dcc8';PILE='#a88f80'
DRAIN='#5b84a8';BEARING_PAD='#4a4045';TEXT='#3b2421';MUTED='#7d6460'

VIA_LEGEND=[(RAIL,'Trilhos'),(GUARD_RAIL,'Contratrilhos'),(SLEEPER,'Dormentes e fixações'),
    (BALLAST,'Lastro'),(CURB,'Paralastro')]
OTHER_LEGEND=[(DRAIN,'Drenagem do tabuleiro'),(CONCRETE_DARK,'Estrutura (tabuleiro, travessa, pilar, bloco)'),
    (BEARING_PAD,'Aparelhos de apoio'),(PILE,'Estacas')]


def _num(value,digits=2):
    text=f'{value:,.{digits}f}'
    return text.replace(',','X').replace('.',',').replace('X','.')


def _rect(x,y,w,h,fill,extra=''):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w,0):.1f}" height="{max(h,0):.1f}" fill="{fill}" {extra}/>'


def _text(x,y,value,size=12,anchor='start',weight='400',fill=TEXT):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" '
        f'font-weight="{weight}" fill="{fill}">{escape(str(value))}</text>')


def _line(x1,y1,x2,y2,stroke=MUTED,width=1,extra=''):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" {extra}/>'


def _dimension(x1,y1,x2,y2,label,offset_text=(0,-6),anchor='middle'):
    arrow='marker-start="url(#dim-arrow)" marker-end="url(#dim-arrow)"'
    mid=((x1+x2)/2+offset_text[0],(y1+y2)/2+offset_text[1])
    return _line(x1,y1,x2,y2,TEXT,1,arrow)+_text(mid[0],mid[1],label,11,anchor,'600')


# Alturas desenhadas (px) comuns ao corte e à elevação, para o terreno ficar alinhado.
SLAB=14.;GIRDER=34.;BEARING=4.;CAP=20.


def pier_pixels(height):
    """Altura desenhada do pilar: cresce com a altura real, limitada para caber."""
    return max(70.,min(200.,55+5.2*height))


def _track_layout(width,lines):
    """Posição dos eixos das vias e meia-base do lastro, em metros a partir do eixo do tabuleiro.

    Reserva, de cada borda para dentro: guarda-corpo (0,40 m), faixa da drenagem (0,40 m)
    e paralastro (0,20 m). Entrevia de 4,50 m, reduzida só se o tabuleiro for estreito.
    """
    avail=width/2-1.0
    if lines==1:
        base=max(min(2.2,avail),1.0)
        return [0.],base
    spacing=max(3.8,min(4.5,2*(avail-2.2)))
    base=max(min(2.2,avail-spacing/2),1.0)
    return [-spacing/2,spacing/2],base


def _cross_section(p):
    out=[];cx=230.;deck_top=140.
    width=p['width'];lines=p['lines']
    sx=min(30.,340./width);half=width*sx/2
    hp=pier_pixels(p['height'])
    deck_bottom=deck_top+SLAB+GIRDER;cap_top=deck_bottom+BEARING;cap_bottom=cap_top+CAP;ground=cap_bottom+hp
    out.append(_text(20,24,'Corte transversal',15,weight='700'))
    out.append(_text(20,42,('Via dupla' if lines==2 else 'Via singela')+' · '+p['deck_type'],11,fill=MUTED))
    # Terreno.
    out.append(_rect(10,ground,500,92,'url(#soil)'))
    out.append(_line(10,ground,510,ground,'#a1876f',1.5))
    # Faixas do tabuleiro: guarda-corpo na borda, drenagem logo para dentro.
    barrier=max(.40*sx,8.);drain_off=barrier+max(.20*sx,5.)
    # Vigas: a externa fica para dentro do tubo de drenagem, e a travessa cobre todas.
    deck=p['deck_type'];pier=p['pier_type']
    limit=half-drain_off-5
    bearings=[]
    if 'caixão' in deck:
        top_w=2*limit;bottom_w=top_w*.62
        out.append(f'<polygon points="{cx-top_w/2:.1f},{deck_top+SLAB:.1f} {cx+top_w/2:.1f},{deck_top+SLAB:.1f} '
            f'{cx+bottom_w/2:.1f},{deck_bottom:.1f} {cx-bottom_w/2:.1f},{deck_bottom:.1f}" fill="{CONCRETE}" stroke="{CONCRETE_DARK}"/>')
        out.append(_rect(cx-bottom_w/2+10,deck_top+SLAB+6,bottom_w-20,GIRDER-14,'#f3ece6',f'stroke="{CONCRETE_DARK}"'))
        bearings=[(cx-bottom_w/2+8,8),(cx+bottom_w/2-8,8)];support=bottom_w/2
    elif 'Viga U' in deck:
        count=max(2,min(5,round(width/3.6)));uw=min(2.6*sx,2*limit/count-6)
        centers=[cx-limit+uw/2+i*((2*limit-uw)/(count-1)) for i in range(count)]
        for x in centers:
            bw=uw*.72
            out.append(f'<path d="M{x-uw/2:.1f},{deck_top+SLAB:.1f} L{x-bw/2:.1f},{deck_bottom:.1f} L{x+bw/2:.1f},{deck_bottom:.1f} '
                f'L{x+uw/2:.1f},{deck_top+SLAB:.1f} L{x+uw/2-6:.1f},{deck_top+SLAB:.1f} L{x+bw/2-6:.1f},{deck_bottom-7:.1f} '
                f'L{x-bw/2+6:.1f},{deck_bottom-7:.1f} L{x-uw/2+6:.1f},{deck_top+SLAB:.1f} Z" fill="{CONCRETE}" stroke="{CONCRETE_DARK}"/>')
            bearings+=[(x-bw/2+6,6),(x+bw/2-6,6)]
        support=centers[-1]-cx+uw*.36
    else:
        count=max(3,min(8,round(width/2.2)))
        color=STEEL if 'aço' in deck else CONCRETE
        web=4 if 'aço' in deck else 7
        flange_top=min(.45*sx,limit/(count-1)*.8,14.);flange_bottom=min(.32*sx,flange_top*.8)
        outer=limit-flange_top
        for i in range(count):
            x=cx-outer+i*(2*outer/(count-1))
            out.append(_rect(x-flange_top,deck_top+SLAB,2*flange_top,5,color,f'stroke="{CONCRETE_DARK}"'))
            out.append(_rect(x-web/2,deck_top+SLAB+5,web,GIRDER-11,color,f'stroke="{CONCRETE_DARK}"'))
            out.append(_rect(x-flange_bottom,deck_bottom-6,2*flange_bottom,6,color,f'stroke="{CONCRETE_DARK}"'))
            bearings.append((x,max(flange_bottom*1.4,6)))
        support=outer+flange_bottom
    # Laje (por cima das vigas, cobrindo o encontro) e guarda-corpos de concreto nas bordas.
    out.append(_rect(cx-half,deck_top,2*half,SLAB,CONCRETE,f'stroke="{CONCRETE_DARK}"'))
    for side in (-1,1):
        edge=cx+side*half;inner=edge-side*barrier
        out.append(f'<polygon points="{edge:.1f},{deck_top:.1f} {inner:.1f},{deck_top:.1f} {edge-side*barrier*.55:.1f},{deck_top-12:.1f} '
            f'{edge-side*barrier*.45:.1f},{deck_top-30:.1f} {edge:.1f},{deck_top-30:.1f}" fill="{CONCRETE}" stroke="{CONCRETE_DARK}"/>')
    # Aparelhos de apoio (neoprene) entre as vigas e a travessa.
    for x,w in bearings:
        out.append(_rect(x-w/2,deck_bottom,w,BEARING,BEARING_PAD))
    # Via permanente: paralastro, lastro, dormentes, trilhos e contratrilhos.
    axes,base=_track_layout(width,lines)
    tracks=[cx+a*sx for a in axes]
    curb=max(.20*sx,5.)
    curb_left=tracks[0]-base*sx;curb_right=tracks[-1]+base*sx
    for x in (curb_left-curb,curb_right):
        out.append(_rect(x,deck_top-16,curb,16,CURB))
    bh=18
    for x in tracks:
        bottom=base*sx;top=min(max(bottom-.75*sx,1.45*sx),bottom-4)  # talude sempre para fora
        out.append(f'<polygon points="{x-bottom:.1f},{deck_top:.1f} {x+bottom:.1f},{deck_top:.1f} '
            f'{x+top:.1f},{deck_top-bh:.1f} {x-top:.1f},{deck_top-bh:.1f}" fill="url(#ballast)"/>')
        sleeper=2.8*sx
        out.append(_rect(x-sleeper/2,deck_top-bh-5,sleeper,5,SLEEPER))
        gauge=1.6*sx/2
        for side in (-1,1):
            rx=x+side*gauge
            out.append(_rect(rx-3,deck_top-bh-14,6,9,RAIL))
            out.append(_rect(rx-side*7-2,deck_top-bh-12,4,7,GUARD_RAIL))
            out.append(f'<circle cx="{rx+side*6:.1f}" cy="{deck_top-bh-6.5:.1f}" r="1.6" fill="{TEXT}"/>')
    # Travessa: apoia todas as vigas; martelo (mais alta no meio) sobre pilar único, reta no pórtico.
    cap_half=support+5
    if pier=='Pórtico':
        col_w=26;columns=[cx-(cap_half-col_w/2-6),cx+(cap_half-col_w/2-6)]
        out.append(_rect(cx-cap_half,cap_top,2*cap_half,CAP,CONCRETE_DARK))
        pier_top=cap_bottom
    else:
        col_w={'Pilar-parede':max(60.,cap_half*.9),'Pilar único retangular':40.}.get(pier,34.)
        columns=[cx]
        low=max(col_w/2+12,cap_half*.45)
        out.append(f'<polygon points="{cx-cap_half:.1f},{cap_top:.1f} {cx+cap_half:.1f},{cap_top:.1f} {cx+cap_half:.1f},{cap_top+CAP*.6:.1f} '
            f'{cx+low:.1f},{cap_bottom:.1f} {cx-low:.1f},{cap_bottom:.1f} {cx-cap_half:.1f},{cap_top+CAP*.6:.1f}" fill="{CONCRETE_DARK}"/>')
        pier_top=cap_bottom
    for x in columns:
        fill='url(#pier-round)' if pier=='Pilar único circular' else CONCRETE
        out.append(_rect(x-col_w/2,pier_top,col_w,ground-pier_top,fill,f'stroke="{CONCRETE_DARK}"'))
    # Drenagem: ralo junto ao guarda-corpo, tubo atravessa a laje, passa por fora das vigas
    # e da travessa, segue sob a travessa até o pilar e desce colado a ele.
    dx=cx+half-drain_off;col_face=columns[-1]+col_w/2+5
    out.append(_rect(dx-4,deck_top-3,8,3,DRAIN))
    run_y=cap_bottom+8
    if col_face>=dx-4:col_face=dx
    out.append(_line(dx,deck_top,dx,run_y,DRAIN,2))
    if col_face!=dx:out.append(_line(dx,run_y,col_face,run_y,DRAIN,2))
    out.append(_line(col_face,run_y,col_face,ground-8,DRAIN,2,'stroke-dasharray="5 3"'))
    out.append(_rect(col_face-6,ground-8,12,8,DRAIN))
    piles=p['piles'];visible=min(8,piles if piles<4 else math.ceil(piles/2))
    span_cols=max(columns)-min(columns)
    block_w=max(span_cols+col_w+20,visible*22+16);block_h=22
    out.append(_rect(cx-block_w/2,ground,block_w,block_h,CONCRETE_DARK))
    pile_len=62
    for i in range(visible):
        x=cx-block_w/2+12+i*((block_w-24)/max(visible-1,1)) if visible>1 else cx
        out.append(_rect(x-4,ground+block_h,8,pile_len,PILE))
    # Rótulos dos elementos estruturais (à direita).
    lx=420
    labels=[(deck_top-22,'Guarda-corpo',cx+half-barrier*.4),(deck_top+SLAB/2,'Laje de distribuição',cx+half),(deck_top+SLAB+GIRDER/2,'Vigas do tabuleiro',cx+support-2),
        (deck_bottom+BEARING/2,'Aparelhos de apoio',bearings[-1][0]+bearings[-1][1]/2),
        (cap_top+CAP*.35,'Travessa',cx+cap_half),(cap_bottom+hp/2,'Pilar',columns[-1]+col_w/2+12),
        (ground+block_h/2,'Bloco',cx+block_w/2),(ground+block_h+pile_len/2,'Estacas',cx+block_w/2-8)]
    for y,label,x in labels:
        out.append(_line(x,y,lx-4,y,MUTED,.8,'stroke-dasharray="2 2"'))
    # Textos com afastamento mínimo para não se sobreporem.
    last=-99
    for y,label,x in labels:
        ty=max(y+4,last+13);last=ty
        if ty!=y+4:out.append(_line(lx-4,y,lx-1,ty-4,MUTED,.8))
        out.append(_text(lx,ty,label,11))
    out.append(_text(lx,ground+block_h+pile_len/2+18,f"{p['piles']} × Ø {_num(p['pile_diameter'])} m",10,fill=MUTED))
    out.append(_text(lx,ground+block_h+pile_len/2+31,f"prof. {_num(p['depth'])} m",10,fill=MUTED))
    # Rótulos da via permanente (acima).
    rail_x=tracks[0]-1.6*sx/2
    out.append(_line(rail_x,deck_top-33,rail_x-12,deck_top-46,RAIL,1))
    out.append(_text(rail_x-14,deck_top-48,'Via permanente',11,'end','700',RAIL))
    # Cotas.
    out.append(_dimension(cx-half,deck_top-66,cx+half,deck_top-66,
        f"Largura do tabuleiro: {_num(width)} m",offset_text=(0,-6)))
    out.append(_line(cx-half,deck_top-70,cx-half,deck_top-32,MUTED,.6))
    out.append(_line(cx+half,deck_top-70,cx+half,deck_top-32,MUTED,.6))
    hx=min(cx-half,cx-block_w/2)-18
    out.append(_line(hx-4,deck_bottom,cx-support,deck_bottom,MUTED,.6))
    out.append(_dimension(hx,deck_bottom,hx,ground,'',offset_text=(0,0)))
    out.append(f'<text x="{hx-6:.1f}" y="{(deck_bottom+ground)/2:.1f}" font-size="11" font-weight="600" fill="{TEXT}" '
        f'text-anchor="middle" transform="rotate(-90 {hx-6:.1f} {(deck_bottom+ground)/2:.1f})">Altura: {_num(p["height"])} m</text>')
    return out,ground+block_h+pile_len



def _elevation(p,x0=540.):
    out=[];deck_top=140.;deck_h=SLAB+GIRDER;hp=pier_pixels(p['height'])
    cap_top=deck_top+deck_h+BEARING;ground=cap_top+CAP+hp
    span_px=max(90.,min(160.,60+2.2*p['span']))
    shown=max(2,min(4,int(380//span_px)))
    left=x0+60+(380-shown*span_px)/2;right=left+shown*span_px
    out.append(_text(x0+10,24,'Elevação longitudinal (trecho típico)',15,weight='700'))
    summary=f"{p['spans']} vãos · {p['supports']} apoios" if p.get('spans') else 'Vãos e apoios calculados no resultado'
    if p.get('km'):summary+=f" · {_num(p['km'],3)} km de corredor"
    out.append(_text(x0+10,42,summary,11,fill=MUTED))
    out.append(_rect(x0,ground,460,92,'url(#soil)'))
    out.append(_line(x0,ground,x0+460,ground,'#a1876f',1.5))
    # Via sobre o tabuleiro.
    out.append(_rect(left-18,deck_top-12,right-left+36,8,'url(#ballast)'))
    out.append(_rect(left-18,deck_top-15,right-left+36,3,SLEEPER))
    out.append(_rect(left-18,deck_top-19,right-left+36,4,RAIL))
    out.append(_rect(left-18,deck_top-4,right-left+36,4,CURB))
    out.append(_rect(left-18,deck_top,right-left+36,deck_h,CONCRETE,f'stroke="{CONCRETE_DARK}"'))
    for i in range(shown):
        out.append(_line(left+i*span_px+span_px,deck_top,left+i*span_px+span_px,deck_top+deck_h,CONCRETE_DARK,1,'stroke-dasharray="3 2"'))
    for i in range(shown+1):
        x=left+i*span_px
        # Travessa com os aparelhos de apoio dos dois vãos que chegam ao pilar (junta no meio).
        out.append(_rect(x-16,cap_top,32,CAP,CONCRETE_DARK))
        for bx in (x-8,x+8):
            out.append(_rect(bx-4,deck_top+deck_h,8,BEARING,BEARING_PAD))
        out.append(_rect(x-8,cap_top+CAP,16,ground-(cap_top+CAP),CONCRETE,f'stroke="{CONCRETE_DARK}"'))
        out.append(_rect(x-20,ground,40,16,CONCRETE_DARK))
        for dx in (-12,0,12):
            out.append(_rect(x+dx-2.5,ground+16,5,46,PILE))
        out.append(_line(x+11,cap_top+CAP+2,x+11,ground-3,DRAIN,1.5,'stroke-dasharray="4 3"'))
    # Cotas do vão e da altura.
    dim_y=ground+80
    out.append(_line(left,ground+66,left,dim_y+4,MUTED,.6));out.append(_line(left+span_px,ground+66,left+span_px,dim_y+4,MUTED,.6))
    out.append(_dimension(left,dim_y,left+span_px,dim_y,f"Vão: {_num(p['span'])} m",offset_text=(0,-5)))
    hx=left-34
    out.append(_line(hx-4,deck_top+deck_h,left-16,deck_top+deck_h,MUTED,.6))
    out.append(_dimension(hx,deck_top+deck_h,hx,ground,''))
    out.append(f'<text x="{hx-6:.1f}" y="{(deck_top+deck_h+ground)/2:.1f}" font-size="11" font-weight="600" fill="{TEXT}" '
        f'text-anchor="middle" transform="rotate(-90 {hx-6:.1f} {(deck_top+deck_h+ground)/2:.1f})">Altura: {_num(p["height"])} m</text>')
    return out


def _legend(y):
    out=[];x=20
    out.append(_text(x,y,'Via permanente em destaque:',11,weight='700',fill=RAIL))
    x=190
    for color,label in VIA_LEGEND:
        out.append(_rect(x,y-10,12,12,color,'rx="2"'));out.append(_text(x+17,y,label,11));x+=17+7*len(label)+18
    y+=22;x=20
    for color,label in OTHER_LEGEND:
        out.append(_rect(x,y-10,12,12,color,'rx="2"'));out.append(_text(x+17,y,label,11));x+=17+6.6*len(label)+22
    out.append(_text(1000,y+22,'Desenho esquemático, sem escala. Cotas = valores do cenário.',10,'end',fill=MUTED))
    return out


def drawing_parameters(scenario,elevated=None):
    """Monta os parâmetros do desenho a partir do cenário (e do resultado, se houver).

    Com trechos homogêneos, desenha o trecho mais extenso.
    """
    lines=int(scenario.get('lines',1))
    width=float(scenario['elevated_width_single'] if lines==1 else scenario['elevated_width_double'])
    params={'lines':lines,'width':width,'height':float(scenario['elevated_height']),
        'span':float(scenario['elevated_span']),'piles':int(scenario['piles_per_support']),
        'pile_diameter':float(scenario['pile_diameter']),'depth':float(scenario['foundation_depth']),
        'deck_type':scenario.get('deck_type','Vigas pré-moldadas com laje'),
        'pier_type':scenario.get('pier_type','Pilar único circular'),'km':float(scenario.get('km',0) or 0)}
    segments=[row for row in (scenario.get('elevated_segments') or []) if isinstance(row,dict)]
    if len(segments)>1:
        longest=max(segments,key=lambda row:float(row.get('Extensão (km)',0) or 0))
        params.update(height=float(longest.get('Altura (m)',params['height'])),
            span=float(longest.get('Vão (m)',params['span'])),
            piles=int(longest.get('Estacas/apoio',params['piles'])),
            pile_diameter=float(longest.get('Diâmetro (m)',params['pile_diameter'])),
            depth=float(longest.get('Profundidade (m)',params['depth'])),
            segment=str(longest.get('Trecho','')))
    if elevated:
        params.update(spans=elevated.get('spans'),supports=elevated.get('supports'))
    return params


def elevated_svg(params):
    """SVG completo (corte + elevação + legenda), pronto para st.markdown."""
    p=dict(params)
    p['width']=max(float(p['width']),1.)
    body,bottom=_cross_section(p)
    body+=_elevation(p)
    legend_y=bottom+44
    body+=_legend(legend_y)
    total_h=legend_y+54
    defs=(f'<defs><marker id="dim-arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{TEXT}"/></marker>'
        f'<pattern id="ballast" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="{BALLAST}"/>'
        f'<circle cx="2" cy="2" r="1.3" fill="#d99a2b"/><circle cx="6" cy="6" r="1.1" fill="#d99a2b"/></pattern>'
        f'<pattern id="soil" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="10" height="10" fill="{SOIL}"/>'
        f'<line x1="0" y1="0" x2="0" y2="10" stroke="#d6c4a8" stroke-width="3"/></pattern>'
        f'<linearGradient id="pier-round" x1="0" x2="1"><stop offset="0" stop-color="{CONCRETE_DARK}"/>'
        f'<stop offset=".45" stop-color="#efe6e0"/><stop offset="1" stop-color="{CONCRETE_DARK}"/></linearGradient></defs>')
    title='Desenho esquemático do elevado: corte transversal e elevação longitudinal'
    return (f'<svg class="elevated-drawing" viewBox="0 0 1010 {total_h:.0f}" width="100%" role="img" '
        f'aria-label="{escape(title)}" xmlns="http://www.w3.org/2000/svg" '
        f'style="font-family:\'Source Sans Pro\',\'Segoe UI\',sans-serif;background:#fffdf8;border:1px solid #f1dfc0;border-radius:12px">'
        f'<title>{escape(title)}</title>{defs}{"".join(body)}</svg>')
