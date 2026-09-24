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
    bdi: float=0.2784182802164763
    months: int=0

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
    ctx={**rules['parameters'],**rules['constants'],**asdict(p),'trainsets':float(p.trainsets),'envelope':model['envelope'],
         'duration':duration,'span':model['span'],'height':model['height']}
    for name,expression in rules['derived']:ctx[name]=evaluate(expression,ctx)
    items=[]
    for r in rules['rules']:
        if not selected(r,p):continue
        q=evaluate(r['quantity'],ctx)
        if q<0:raise ValueError('Quantidade negativa: '+r['label']+'. Revise extensão e premissas.')
        if q==0:continue
        price=resolve_price(r['candidates'],catalog,rules['source_priority'])
        if r['unit']!=price['unit']:raise ValueError('Unidade incompatível: '+r['id'])
        items.append({'id':r['id'],'eap':r['eap'],'group':r['group'],'label':r['label'],
                      'code':price['code'],'source':price['source'],'description':price['description'],
                      'unit':price['unit'],'quantity':q,'unit_cost':price['price'],
                      'total':money(q*price['price']),'price_key':price['key'],'date':price['date'],
                      'quantity_formula':r['quantity'],'original_formula':r['original_formula'],
                      'note':r['note'],'origin':r['origin'],'sheet':r['sheet'],'row':r['row'],
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
    return {'scenario':asdict(p),'model_label':model['label'],'duration':duration,'items':items,'groups':groups,
            'direct':direct,'bdi_amount':bdi,'total':total,'per_km':money(total/p.km),'per_line_km':money(total/(p.km*p.lines)),
            'counts':dict(Counter(x['source'] for x in items)),'warnings':warnings,'rule_version':rules['version'],
            'derived':rules['derived'],
            'context':{k:v for k,v in ctx.items() if isinstance(v,(int,float))}}
