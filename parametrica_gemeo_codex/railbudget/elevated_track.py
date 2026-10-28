"""Custo paramétrico da via permanente no elevado, por componente, e sua sensibilidade.

Só lê o orçamento já calculado: agrupa itens existentes (mesmos preços e quantidades)
e divide pelos indicadores físicos (km de via e metro de viaduto). Nenhum preço novo.
"""
from dataclasses import replace

from .elevated import DECK_FACTORS, DECK_LABELS, FOUNDATION_LABELS, PIER_LABELS, calculate_elevated
from .expressions import money

# (componente, prefixo do grupo, rótulos dos itens). AMV usa o grupo inteiro.
TRACK_COMPONENTS=[
    ('Trilhos','1 ',{'Trilhos'}),
    ('Fixações','1 ',{'Fixações'}),
    ('Dormentes','1 ',{'Dormentes'}),
    ('Lastro e paralastro','1 ',{'Lastro','Transporte do lastro','Paralastro'}),
    ('Montagem, soldagem e geometria','1 ',{'Montagem','Regularização','Geometria final','Soldagem','Controle de soldas'}),
    ('Contratrilhos de segurança','1 ',{'Contratrilhos de segurança','Montagem dos contratrilhos'}),
    ('AMVs','5 ',None),
    ('Drenagem do tabuleiro','3 ',{'Canaletas no tabuleiro','Descidas do tabuleiro DN100','Caixas nos pés dos pilares'}),
]
STRUCTURE_LABELS=FOUNDATION_LABELS|PIER_LABELS|DECK_LABELS
SPAN_VALUES=(10.,15.,20.,25.,30.,35.,40.,45.)
HEIGHT_VALUES=(3.,6.,9.,12.,15.,20.,25.,30.)


def _plain(item):
    return item['label'].split(' · ')[-1]


def _component_of(item):
    for name,group,labels in TRACK_COMPONENTS:
        if item['group'].startswith(group) and (labels is None or _plain(item) in labels):
            return name
    return None


def _measures(scenario):
    km=float(scenario['km']);lines=int(scenario['lines'])
    return km*lines,km*1000


def track_breakdown(result):
    """Custo direto da via permanente do elevado por componente.

    Respeita o recorte de grupos do resultado (itens de grupos desmarcados já não estão em items).
    """
    totals={name:0. for name,_,_ in TRACK_COMPONENTS}
    for item in result['items']:
        name=_component_of(item)
        if name:totals[name]+=item['total']
    track_km,viaduct_m=_measures(result['scenario'])
    direct=money(sum(totals.values()));bdi=result['scenario']['bdi']
    rows=[{'Componente':name,'Custo direto (R$)':money(value),
        'R$/km de via':money(value/track_km),'R$/m de viaduto':money(value/viaduct_m),
        'Participação (%)':100*value/direct if direct else 0.} for name,value in totals.items()]
    return {'rows':rows,'direct':direct,'with_bdi':money(direct*(1+bdi)),
        'per_track_km':money(direct/track_km),'per_viaduct_m':money(direct/viaduct_m),
        'per_track_km_with_bdi':money(direct*(1+bdi)/track_km),
        'share_of_direct':100*direct/result['direct'] if result['direct'] else 0.,
        'track_km':track_km,'viaduct_m':viaduct_m}


def _point(p,rules,catalog,segments,groups):
    result=calculate_elevated(p,rules,catalog,segments)
    items=[item for item in result['items'] if groups is None or item['group'] in groups]
    track=sum(item['total'] for item in items if _component_of(item))
    structure=sum(item['total'] for item in items if item['group'].startswith('1 ') and _plain(item) in STRUCTURE_LABELS)
    track_km,viaduct_m=_measures(result['scenario'])
    return {'Via permanente (R$/m)':money(track/viaduct_m),'Estrutura do viaduto (R$/m)':money(structure/viaduct_m),
        'Via permanente (R$/km de via)':money(track/track_km)}


def track_sensitivity(p,rules,catalog,segments=None,groups=None):
    """Varre vão, altura, tipologia do tabuleiro e nº de vias, mantendo as demais premissas.

    Com trechos homogêneos, o valor testado de vão ou altura vale para todos os trechos.
    Devolve linhas com 'Variável', 'Valor', 'Ordem' e os custos por metro e por km de via.
    """
    segments=list(segments or p.elevated_segments or [])
    if len(segments)==1:
        row=segments[0]
        p=replace(p,elevated_height=float(row.get('Altura (m)',p.elevated_height)),
            elevated_span=float(row.get('Vão (m)',p.elevated_span)),
            foundation_type=str(row.get('Fundação',p.foundation_type)),
            pile_diameter=float(row.get('Diâmetro (m)',p.pile_diameter)),
            foundation_depth=float(row.get('Profundidade (m)',p.foundation_depth)),
            piles_per_support=int(row.get('Estacas/apoio',p.piles_per_support)),
            urban_interference=str(row.get('Interferência',p.urban_interference)))
    segments=segments if len(segments)>1 else None
    p=replace(p,elevated_segments=())
    rows=[]
    def add(variable,label,order,scenario,rows_segments):
        try:point=_point(scenario,rules,catalog,rows_segments,groups)
        except ValueError:return
        rows.append({'Variável':variable,'Valor':label,'Ordem':order,**point})
    for value in SPAN_VALUES:
        add('Vão (m)',value,value,replace(p,elevated_span=value),
            [{**row,'Vão (m)':value} for row in segments] if segments else None)
    for value in HEIGHT_VALUES:
        add('Altura dos pilares (m)',value,value,replace(p,elevated_height=value),
            [{**row,'Altura (m)':value} for row in segments] if segments else None)
    for order,deck in enumerate(DECK_FACTORS):
        add('Tipologia do tabuleiro',deck,order,replace(p,deck_type=deck),segments)
    for lines in (1,2):
        add('Via',('Singela' if lines==1 else 'Dupla'),lines,replace(p,lines=lines),segments)
    return rows
