from dataclasses import asdict
import xml.etree.ElementTree as ET

from railbudget.engine import Scenario
from railbudget.elevated_drawing import RAIL, drawing_parameters, elevated_svg


def svg_for(**changes):
    scenario=asdict(Scenario(configuration='Elevado',rolling_stock=False,**changes))
    return elevated_svg(drawing_parameters(scenario,{'spans':50,'supports':51}))


def test_desenho_e_svg_valido_com_cotas_do_cenario():
    svg=svg_for()
    ET.fromstring(svg)
    assert 'Corte transversal' in svg and 'Elevação longitudinal' in svg
    assert 'Largura do tabuleiro: 7,00 m' in svg
    assert 'Altura: 8,00 m' in svg and 'Vão: 20,00 m' in svg
    assert '50 vãos · 51 apoios' in svg
    assert 'Via permanente em destaque' in svg


def test_desenho_muda_com_vias_altura_vao_e_tipologias():
    single=svg_for();double=svg_for(lines=2)
    # Via dupla desenha dois trilhos a mais no corte transversal.
    assert double.count(f'fill="{RAIL}"')-single.count(f'fill="{RAIL}"')==2
    assert 'Largura do tabuleiro: 11,00 m' in double and 'Via dupla' in double
    tall=svg_for(elevated_height=20,elevated_span=35)
    assert 'Altura: 20,00 m' in tall and 'Vão: 35,00 m' in tall
    assert tall!=single
    assert '<polygon' in svg_for(deck_type='Viga-caixão moldada no local')
    portico=svg_for(pier_type='Pórtico');parede=svg_for(pier_type='Pilar-parede')
    assert portico!=parede!=single


def test_desenho_com_trechos_usa_o_trecho_mais_extenso():
    scenario=asdict(Scenario(configuration='Elevado',rolling_stock=False))
    scenario['elevated_segments']=[
        {'Trecho':'Curto','Extensão (km)':.3,'Altura (m)':6,'Vão (m)':20,'Estacas/apoio':4,'Diâmetro (m)':.8,'Profundidade (m)':18},
        {'Trecho':'Longo <b>','Extensão (km)':.7,'Altura (m)':14,'Vão (m)':30,'Estacas/apoio':8,'Diâmetro (m)':.41,'Profundidade (m)':25}]
    params=drawing_parameters(scenario)
    assert params['height']==14 and params['span']==30 and params['piles']==8
    svg=elevated_svg(params)
    ET.fromstring(svg)
    assert '8 × Ø 0,41 m' in svg and 'prof. 25,00 m' in svg


def _shapes(svg,fill):
    """Caixas (x0,y0,x1,y1) dos retângulos e polígonos do corte transversal com a cor `fill`."""
    from railbudget.drawing_image import _floats
    out=[]
    for el in ET.fromstring(svg).iter():
        tag=el.tag.split('}')[-1]
        if el.get('fill')!=fill:continue
        if tag=='rect':
            x,y,w,h=(float(el.get(k)) for k in ('x','y','width','height'));box=(x,y,x+w,y+h)
        elif tag=='polygon':
            n=_floats(el.get('points'));xs=n[0::2];ys=n[1::2];box=(min(xs),min(ys),max(xs),max(ys))
        else:continue
        if box[2]<520:out.append(box)
    return out


def test_todas_as_vigas_apoiam_na_travessa_em_qualquer_tipologia():
    from railbudget.elevated import DECK_FACTORS, PIER_FACTORS
    from railbudget.elevated_drawing import BEARING_PAD, CONCRETE_DARK
    for lines,width in ((1,4),(1,7),(1,12),(2,8),(2,10.5),(2,11),(2,20)):
        key='elevated_width_single' if lines==1 else 'elevated_width_double'
        for deck in DECK_FACTORS:
            for pier in PIER_FACTORS:
                svg=svg_for(lines=lines,deck_type=deck,pier_type=pier,**{key:width})
                bearings=_shapes(svg,BEARING_PAD)
                assert len(bearings)>=2
                cap_top=bearings[0][3]
                caps=[b for b in _shapes(svg,CONCRETE_DARK) if abs(b[1]-cap_top)<.2]
                assert len(caps)==1,(lines,width,deck,pier)
                cap=caps[0]
                for b in bearings:
                    assert abs(b[3]-cap_top)<.2 and cap[0]<=b[0] and b[2]<=cap[2],(lines,width,deck,pier,b,cap)
