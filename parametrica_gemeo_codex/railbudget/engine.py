from dataclasses import dataclass, asdict
from collections import Counter
import json
import math
import sqlite3
from pathlib import Path
from .expressions import evaluate, money

ROOT=Path(__file__).resolve().parents[1]

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
    profile: str='siec'
    bdi: float=0.2784182802164763
    months: int=0

def load_model(root=ROOT):
    root=Path(root)
    rules=json.loads((root/'config/rules.json').read_text(encoding='utf-8'))
    with sqlite3.connect(root/'data/catalog.sqlite') as con:
        con.row_factory=sqlite3.Row
        catalog={r['key']:dict(r) for r in con.execute('SELECT * FROM prices')}
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
    for value,options,name in [(p.configuration,['Superfície','Elevado'],'configuração'),(p.lines,[1,2],'número de linhas'),
       (p.drainage,['Normal','Reforçada','Complexa'],'drenagem'),(p.fence,['Cerca','Muro','Nenhuma'],'vedação'),
       (p.profile,rules['profiles'],'modelo')]:
        if value not in options:raise ValueError('Valor inválido para '+name)
    if type(p.amvs) is not int or p.amvs<0:raise ValueError('Quantidade de AMVs deve ser inteira e não negativa.')
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
    if g=='6':return p.ducts
    return True

def calculate(p,rules,catalog):
    """Função pura: entradas + dados imutáveis → resultado, sem I/O/Streamlit."""
    validate(p,rules)
    model=rules['profiles'][p.profile]
    duration=p.months or model['elevated_months' if p.configuration=='Elevado' else 'surface_months']
    ctx={**rules['parameters'],**rules['constants'],**asdict(p),'envelope':model['envelope'],
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
    if p.ducts:warnings.append('Banco de seis dutos ao nível do solo, inclusive no elevado; cabos, subidas e interfaces ativas não incluídos.')
    if p.drainage=='Complexa':warnings.append('Bombeamento por estação de referência; capacidade hidráulica e alimentação externa não dimensionadas. Anúncio do quadro estava esgotado.')
    return {'scenario':asdict(p),'model_label':model['label'],'duration':duration,'items':items,'groups':groups,
            'direct':direct,'bdi_amount':bdi,'total':total,'per_km':money(total/p.km),'per_line_km':money(total/(p.km*p.lines)),
            'counts':dict(Counter(x['source'] for x in items)),'warnings':warnings,'rule_version':rules['version'],
            'derived':rules['derived'],
            'context':{k:v for k,v in ctx.items() if isinstance(v,(int,float))}}
