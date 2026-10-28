from dataclasses import dataclass, asdict
from collections import Counter
import json
import math
import sqlite3
import re
from pathlib import Path
from copy import deepcopy
from .expressions import evaluate, money

ROOT=Path(__file__).resolve().parents[1]

def public_provenance(value):
    """Preserva a referência técnica sem expor caminhos locais ou URLs."""
    if not value:return ''
    try:
        parsed=json.loads(value)
    except (TypeError,json.JSONDecodeError):
        return 'Referência registrada na base técnica.' if re.search(r'(?i)([a-z]:\\|/users/|https?://|file://)',str(value)) else str(value)
    if isinstance(parsed,list):
        clean=[]
        for entry in parsed:
            if isinstance(entry,dict):
                clean.append({k:entry[k] for k in ('sheet','row','original_row') if k in entry})
        return json.dumps(clean,ensure_ascii=False)
    return 'Referência registrada na base técnica.'

def select_groups(result, selected_groups, bdi_rate=None):
    """Recorte financeiro puro; conserva as quantidades do cenário calculado."""
    chosen=set(selected_groups)
    if chosen-set(result['groups']):
        raise ValueError('Grupo de orçamento desconhecido.')
    out=deepcopy(result)
    rate=result['scenario']['bdi'] if bdi_rate is None else bdi_rate
    if not math.isfinite(rate) or not 0<=rate<=1:
        raise ValueError('BDI deve estar entre 0% e 100%.')
    out['scenario']['bdi']=rate
    out['context']['bdi']=rate
    out['items']=[x for x in out['items'] if x['group'] in chosen]
    out['groups']={g:v if g in chosen else 0.0 for g,v in result['groups'].items()}
    direct=money(sum(out['groups'].values()))
    bdi=money(direct*rate)
    total=money(direct+bdi)
    km=result['scenario']['km']
    out.update(direct=direct,bdi_amount=bdi,total=total,per_km=money(total/km),
               per_line_km=money(total/(km*result['scenario']['lines'])),
               counts=dict(Counter(x['source'] for x in out['items'])),
               selected_groups=[g for g in result['groups'] if g in chosen])
    out['scope_summary']=[{'group':g,'selected':g in chosen,'direct':v,
        'per_km':money(v/km),'share':100*v/direct if direct and g in chosen else 0.0}
        for g,v in result['groups'].items()]
    for group in out['scope_summary']:
        group['bdi_amount']=money(group['direct']*rate)
    included=[g for g in out['scope_summary'] if g['selected'] and g['direct']]
    if included:
        included[-1]['bdi_amount']=money(included[-1]['bdi_amount']+bdi-sum(g['bdi_amount'] for g in included))
    for group in out['scope_summary']:
        group['total']=money(group['direct']+group['bdi_amount'])
        group['per_km_with_bdi']=money(group['total']/km)
    # Indicadores derivados do recorte: frota separada da infraestrutura e via total da shortline.
    fleet=money(sum(g['total'] for g in out['scope_summary'] if g['selected'] and g['group'].startswith('9 ')))
    out['fleet_total']=fleet
    out['per_km_without_fleet']=money((total-fleet)/km)
    track_km=result['scenario'].get('track_km')
    if track_km:
        out['per_track_km']=money(total/track_km)
    if chosen!=set(result['groups']):
        out['warnings'].append('Recorte financeiro: grupos incluídos no total: '+
            (', '.join(out['selected_groups']) or 'nenhum')+
            '. Quantidades e geometria permanecem as do cenário calculado; excluir um grupo não redimensiona os demais.')
    return out

@dataclass(frozen=True)
class Scenario:
    km: float=1.0
    configuration: str='Superfície'
    lines: int=1
    drainage: str='Reforçada'
    fence: str='Cerca'
    amvs: int=1
    ducts: bool=True
    topography: bool=True
    overhead: bool=True
    signaling: bool=True
    detection: str='Circuito de via'
    rolling_stock: bool=True
    trainsets: int=1
    profile: str='siec'
    bdi: float=0.263
    months: int=0
    elevated_height: float=8.0
    elevated_span: float=20.0
    elevated_width_single: float=7.0
    elevated_width_double: float=11.0
    foundation_type: str='Hélice contínua'
    foundation_depth: float=20.0
    piles_per_support: int=4
    pile_diameter: float=0.80
    urban_interference: str='Média'
    elevated_segments: tuple=()
    deck_type: str='Vigas pré-moldadas com laje'
    pier_type: str='Pilar único circular'
    geotechnical_condition: str='Intermediária'
    construction_method: str='Montagem com guindaste'
    execution_constraint: str='Frente livre'
    special_span_length: float=0.0
    special_span_addition: float=50.0
    transitions: int=0
    transition_unit_cost: float=2000000.0
    noise_barrier_length: float=0.0
    noise_barrier_height: float=3.0
    noise_barrier_unit_cost: float=2500.0


FOUNDATION_OPTIONS={
    'Hélice contínua':{
        'mobilization':'SIEC-02.01.04.400.01',
        'piles':{.25:'SIEC-02.01.04.400.02',.30:'SIEC-02.01.04.400.03',
            .35:'SIEC-02.01.04.400.04',.40:'SIEC-02.01.04.400.05',
            .50:'SIEC-02.01.04.400.06',.60:'SIEC-02.01.04.400.07',
            .70:'SIEC-02.01.04.400.08',.80:'SIEC-02.01.04.400.09',
            .90:'SIEC-02.01.04.400.10'},
    },
    'Estaca raiz':{
        'mobilization':'SIEC-02.01.04.500.01',
        'piles':{.16:'SIEC-02.01.04.500.11',.20:'SIEC-02.01.04.500.12',
            .25:'SIEC-02.01.04.500.13',.31:'SIEC-02.01.04.500.14',
            .41:'SIEC-02.01.04.500.15',.45:'SIEC-02.01.04.500.16'},
    },
}
FOUNDATION_CAPACITIES={
    'Hélice contínua':{.25:30,.30:45,.35:60,.40:80,.50:130,.60:160,.70:220,.80:290,.90:360},
    'Estaca raiz':{.16:35,.20:50,.25:70,.31:100,.41:150,.45:200},
}


def foundation_diameters(kind):
    return tuple(FOUNDATION_OPTIONS[kind]['piles'])


def foundation_capacity(kind,diameter):
    match=min(FOUNDATION_CAPACITIES[kind],key=lambda value:abs(value-diameter))
    return FOUNDATION_CAPACITIES[kind][match]


def _catalog_key_by_code(catalog,code):
    matches=[key for key,row in catalog.items() if row.get('code')==code and row.get('price') is not None]
    if not matches:raise ValueError('A base ativa não possui o serviço de fundação '+code+'.')
    return matches[0]

def load_model(root=ROOT):
    root=Path(root)
    rules=json.loads((root/'config/rules.json').read_text(encoding='utf-8'))
    with sqlite3.connect(root/'data/catalog.sqlite') as con:
        con.row_factory=sqlite3.Row
        catalog={r['key']:{**dict(r),'provenance':public_provenance(r['provenance'])} for r in con.execute('SELECT * FROM prices')}
    extra=root/'data/scope2_prices.json'
    if extra.exists():
        for row in json.loads(extra.read_text(encoding='utf-8')):
            catalog[row['key']]={**row,'provenance':public_provenance(row.get('provenance',''))}
    return rules,catalog

def resolve_price(candidates,catalog,priority):
    available=[catalog[k] for k in candidates if k in catalog and catalog[k]['price'] is not None]
    if not available:raise ValueError('Preço ausente para: '+', '.join(candidates))
    ordered=sorted(available,key=lambda r:priority.index(r['source']))
    chosen=ordered[0]
    if chosen['price']<0 or not math.isfinite(chosen['price']):raise ValueError('Preço inválido: '+chosen['code'])
    return chosen

def validate(p,rules):
    if not math.isfinite(p.km) or not 0.01<=p.km<=10000:raise ValueError('Extensão deve estar entre 0,01 e 10.000 km.')
    if p.configuration=='Subterrâneo':
        raise ValueError('O orçamento subterrâneo ainda precisa de quantitativos e preços específicos de túneis e sistemas associados.')
    for value,options,name in [(p.configuration,['Superfície','Elevado'],'configuração'),(p.lines,[1,2],'número de linhas'),
       (p.drainage,['Normal','Reforçada','Complexa'],'drenagem'),(p.fence,['Cerca','Muro','Nenhuma'],'vedação'),
       (p.detection,['Circuito de via','Contador de eixos'],'detecção de trens'),
       (p.profile,rules['profiles'],'modelo')]:
        if value not in options:raise ValueError('Valor inválido para '+name)
    if type(p.amvs) is not int or p.amvs<0:raise ValueError('Quantidade de AMVs deve ser inteira e não negativa.')
    if type(p.trainsets) is not int or not 0<=p.trainsets<=10000:raise ValueError('Quantidade de composições deve ser inteira entre 0 e 10.000.')
    if type(p.months) is not int or not 0<=p.months<=1200:raise ValueError('Prazo inválido.')
    if not math.isfinite(p.bdi) or not 0<=p.bdi<=1:raise ValueError('BDI deve estar entre 0% e 100%.')
    if p.configuration=='Elevado' and p.profile=='siec':
        numeric=[(p.elevated_height,3,30,'altura média dos pilares'),
            (p.elevated_span,10,45,'distância entre pilares'),
            (p.elevated_width_single,4,12,'largura do tabuleiro da via singela'),
            (p.elevated_width_double,8,20,'largura do tabuleiro da via dupla'),
            (p.foundation_depth,5,60,'profundidade das fundações')]
        for value,minimum,maximum,name in numeric:
            if not math.isfinite(value) or not minimum<=value<=maximum:
                raise ValueError(f'{name.capitalize()} deve estar entre {minimum} e {maximum} m.')
        if p.foundation_type not in FOUNDATION_OPTIONS:raise ValueError('Tipo de fundação profunda inválido.')
        if type(p.piles_per_support) is not int or not 2<=p.piles_per_support<=16:
            raise ValueError('Quantidade de estacas por apoio deve ser inteira entre 2 e 16.')
        if not any(math.isclose(p.pile_diameter,value,abs_tol=1e-8)
            for value in foundation_diameters(p.foundation_type)):
            raise ValueError('Diâmetro indisponível na base SIEC para a fundação selecionada.')
        if p.urban_interference not in ('Baixa','Média','Alta'):
            raise ValueError('Nível de interferência urbana inválido.')
    if math.ceil(p.amvs/p.lines)*rules['profiles'][p.profile]['envelope']>=p.km*1000:
        raise ValueError('Os envelopes dos AMVs ocupam toda a extensão de uma linha. Aumente a extensão ou reduza os AMVs.')

def selected(r,p):
    if r['profile'] not in (p.profile,'both') or r['configuration'] not in (None,p.configuration):return False
    g=r['group'][0];v=r['variant']
    if g=='1' and p.profile=='legacy':return v==('1.1.' if p.configuration=='Elevado' else '1.2.')+str(p.lines)
    if g=='2':return p.topography and v==('E' if p.configuration=='Elevado' else 'S')+str(p.lines)
    if g=='3':return v=={'Normal':'3.1','Reforçada':'3.2','Complexa':'3.3'}[p.drainage] or (v=='3.E' and p.configuration=='Elevado')
    if g=='4':return v=={'Cerca':'4.1','Muro':'4.2','Nenhuma':None}[p.fence]
    if g=='5':return p.amvs>0 and (p.profile=='siec' or v==('5.E' if p.configuration=='Elevado' else '5.S'))
    if g=='6':
        if not p.ducts:return False
        if p.profile=='legacy':return v=='6.S'
        return v==('6.E' if p.configuration=='Elevado' else '6.S')
    if g=='7':return p.overhead
    if g=='8':
        if not p.signaling:return False
        if v=='8.C':return p.detection=='Circuito de via'
        if v=='8.E':return p.detection=='Contador de eixos'
        if v=='8.A':return p.amvs>0
        return True
    if g=='9':return p.rolling_stock and p.trainsets>0
    return True

def calculate(p,rules,catalog):
    """Função pura: entradas + dados imutáveis → resultado, sem I/O/Streamlit."""
    validate(p,rules)
    model=rules['profiles'][p.profile]
    duration=p.months or model['elevated_months' if p.configuration=='Elevado' else 'surface_months']
    parametric_elevated=p.configuration=='Elevado' and p.profile=='siec'
    span=p.elevated_span if parametric_elevated else model['span']
    height=p.elevated_height if parametric_elevated else model['height']
    ctx={**rules['parameters'],**rules['constants'],**asdict(p),'trainsets':float(p.trainsets),'envelope':model['envelope'],
         'duration':duration,'span':span,'height':height}
    if parametric_elevated:
        ctx['V18']=p.piles_per_support
        ctx['V19']=p.foundation_depth
    for name,expression in rules['derived']:ctx[name]=evaluate(expression,ctx)
    if parametric_elevated:
        active_width=p.elevated_width_single if p.lines==1 else p.elevated_width_double
        default_width=7 if p.lines==1 else 11
        ctx['active_deck_width']=active_width
        ctx['deck_area']=ctx['L']*active_width+p.amvs*model['envelope']*2
        ctx['elevated_height_factor']=p.elevated_height/8
        ctx['foundation_block_factor']=(p.piles_per_support/4)*(p.pile_diameter/.80)**2
        ctx['deck_width_factor']=active_width/default_width
    items=[]
    for r in rules['rules']:
        if not selected(r,p):continue
        q=evaluate(r['quantity'],ctx)
        quantity_formula=r['quantity']
        candidates=r['candidates']
        note=r['note']
        if parametric_elevated and r['id'].startswith('vp:Elevado:'):
            row=int(r['id'].rsplit(':',1)[1])
            if row==19:
                code=FOUNDATION_OPTIONS[p.foundation_type]['mobilization']
                candidates=[_catalog_key_by_code(catalog,code)]
                note=f'Mobilização compatível com {p.foundation_type.lower()}, conforme serviço disponível na base SIEC.'
            elif row==20:
                diameter=min(foundation_diameters(p.foundation_type),key=lambda value:abs(value-p.pile_diameter))
                code=FOUNDATION_OPTIONS[p.foundation_type]['piles'][diameter]
                candidates=[_catalog_key_by_code(catalog,code)]
                note=(f'{p.foundation_type}, diâmetro {diameter:.2f} m e profundidade média de '
                    f'{p.foundation_depth:.2f} m; quantidade preliminar sujeita a sondagens e projeto geotécnico.')
            elif row==21:
                q*= (p.pile_diameter/.80)**2
                quantity_formula+='*(pile_diameter/0.80)^2'
            elif 22<=row<=26:
                q*=ctx['foundation_block_factor']
                quantity_formula+='*foundation_block_factor'
            elif 27<=row<=30:
                q*=ctx['elevated_height_factor']
                quantity_formula+='*elevated_height_factor'
            elif row==36:
                q*=ctx['deck_width_factor']
                quantity_formula+='*deck_width_factor'
        if q<0:raise ValueError('Quantidade negativa: '+r['label']+'. Revise extensão e premissas.')
        if q==0:continue
        price=resolve_price(candidates,catalog,rules['source_priority'])
        if r['unit']!=price['unit']:raise ValueError('Unidade incompatível: '+r['id'])
        items.append({'id':r['id'],'eap':r['eap'],'group':r['group'],'label':r['label'],
                      'code':price['code'],'source':price['source'],'description':price['description'],
                      'unit':price['unit'],'quantity':q,'unit_cost':price['price'],
                      'total':money(q*price['price']),'price_key':price['key'],'date':price['date'],
                      'quantity_formula':quantity_formula,'original_formula':r['original_formula'],
                      'note':note,'origin':r['origin'],'sheet':r['sheet'],'row':r['row'],
                      'provenance':price['provenance']})
    items.sort(key=lambda x:rules['groups'].index(x['group']))
    sequence=Counter()
    for item in items:
        group=item['group'].split()[0];sequence[group]+=1
        item['original_eap']=item['eap']
        prefix=('1.1.' if p.configuration=='Elevado' else '1.2.')+str(p.lines) if group=='1' else group
        item['eap']=prefix+'.'+str(sequence[group]).zfill(3)
    groups={g:money(sum(x['total'] for x in items if x['group']==g)) for g in rules['groups']}
    direct=money(sum(x['total'] for x in items));bdi=money(direct*p.bdi);total=money(direct+bdi)
    warnings=['Estimativa paramétrica. Geometria, cargas, geotecnia, hidráulica e interfaces exigem projeto.',
              'As notas da fonte descrevem a referência de 1 km. A quantidade calculada e a fórmula do cenário prevalecem.',
              'O BDI é uma premissa editável; não houve validação tributária nem reajuste das datas-base.']
    if p.profile=='siec' and p.lines==2:warnings.append('Via dupla SIEC extrapolada: entrevia de 4 m e fatores configuráveis de compartilhamento; não há orçamento manual original para esta combinação.')
    if p.profile=='legacy':warnings.append('Perfil legado: preços da via e AMV nº9 são provisões herdadas, sem cotação validada.')
    if p.ducts and p.configuration=='Superfície':warnings.append('Infraestrutura de cabos em superfície: banco subterrâneo de seis dutos. Cabos e interfaces ativas não incluídos.')
    if p.ducts and p.configuration=='Elevado' and p.profile=='siec':warnings.append('Infraestrutura de cabos no elevado: canaletas e passa-fios embutidos no tabuleiro. Não há banco de dutos enterrado nesta configuração; cabos e interfaces ativas não incluídos.')
    if p.ducts and p.configuration=='Elevado' and p.profile=='legacy':warnings.append('Perfil legado: conserva o banco subterrâneo de seis dutos da planilha histórica para reproduzir seu total. Use o modelo SIEC para a solução elevada com canaletas e passa-fios no tabuleiro.')
    if p.drainage=='Complexa':warnings.append('Bombeamento por estação de referência; capacidade hidráulica e alimentação externa não dimensionadas. Anúncio do quadro estava esgotado.')
    if p.overhead:warnings.append('Rede aérea paramétrica: vãos de 50 m, um suporte por linha, dois pontos de tensionamento por trecho de 1,5 km e seccionamento por trecho de 3 km. Projeto eletromecânico define arranjos finais.')
    if p.signaling:warnings.append(f'Sinalização paramétrica com detecção por {p.detection.lower()}, blocos de 500 m e um intertravamento de referência a cada 10 km ou fração.')
    if p.rolling_stock:warnings.append(f'Material rodante: {p.trainsets} composição(ões) de 8 carros pelo custo unitário do contrato CPTM 8186142011, data-base abril/2016. O custo da frota é por composição; o valor por km é somente o rateio pela extensão atendida, sem reajuste monetário.')
    elevated=None
    if parametric_elevated:
        component_rules={
            'Fundações':{'Sondagens','Mobilização fundações','Estacas','Armadura das estacas','Escavação de blocos','Blocos e encontros'},
            'Pilares e travessas':{'Pilares e travessas'},
            'Tabuleiro':{'Aparelhos de apoio','Laje de distribuição','Vigas pré-moldadas','Impermeabilização'},
        }
        structural={name:money(sum(x['total'] for x in items if x['label'] in labels))
            for name,labels in component_rules.items()}
        elevated_group=next((value for group,value in groups.items() if group.startswith('1 ')),0.0)
        structural['Via e proteções do elevado']=money(elevated_group-sum(structural.values()))
        recommendation=('Estaca raiz: tende a ser mais adequada a acessos restritos e locais sensíveis a vibração.'
            if p.urban_interference=='Alta' else
            'Hélice contínua: solução de referência com boa produtividade, condicionada ao acesso do equipamento.'
            if p.urban_interference=='Média' else
            'Hélice contínua: referência inicial; compare produtividade, capacidade e condições geotécnicas.')
        capacity_per_pile=foundation_capacity(p.foundation_type,p.pile_diameter)
        support_capacity=capacity_per_pile*p.piles_per_support
        elevated={'active_width':ctx['active_deck_width'],'spans':int(ctx['spans']),
            'supports':int(ctx['supports']),'total_piles':int(ctx['supports']*p.piles_per_support),
            'total_pile_length':ctx['supports']*p.piles_per_support*p.foundation_depth,
            'nominal_capacity_per_pile':capacity_per_pile,'nominal_capacity_per_support':support_capacity,
            'recommendation':recommendation,'components':structural,
            'reference':{'height':8.0,'span':20.0,'width_single':7.0,'width_double':11.0,
                'foundation_type':'Hélice contínua','foundation_depth':20.0,
                'piles_per_support':4,'pile_diameter':.80}}
        warnings.append('Elevado: fundações, pilares e tabuleiro foram parametrizados sobre a referência SIEC. A solução final depende de sondagens, cargas, geometria e projeto geotécnico e estrutural.')
        if support_capacity<1160:
            warnings.append(f'Fundação selecionada: capacidade nominal declarada de {support_capacity:g} tf por apoio, inferior aos 1.160 tf da referência inicial (4 estacas hélice Ø 0,80 m). Verifique quantidade, cargas e geotecnia.')
    result={'scenario':asdict(p),'model_label':model['label'],'duration':duration,'items':items,'groups':groups,
            'direct':direct,'bdi_amount':bdi,'total':total,'per_km':money(total/p.km),'per_line_km':money(total/(p.km*p.lines)),
            'counts':dict(Counter(x['source'] for x in items)),'warnings':warnings,'rule_version':rules['version'],
            'derived':rules['derived'],
            'context':{k:v for k,v in ctx.items() if isinstance(v,(int,float))}}
    if elevated:result['elevated']=elevated
    return result
