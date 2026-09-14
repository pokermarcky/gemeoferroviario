from pathlib import Path
import copy
import json
import math
import pytest
from railbudget.engine import *
from railbudget.expressions import evaluate, money

@pytest.fixture(scope='module')
def model():return load_model()

@pytest.mark.parametrize('cfg,lines,expected',[('Elevado',1,53552530.02),('Elevado',2,80467223.28),('Superfície',1,13321596.60),('Superfície',2,20597620.85)])
def test_four_manual_complete_budgets(model,cfg,lines,expected):
    r,c=model
    result=calculate(Scenario(profile='legacy',configuration=cfg,lines=lines,amvs=lines),r,c)
    assert result['total']==expected
    for item in result['items']:
        rule=next(z for z in r['rules'] if z['id']==item['id'])
        multiplier=lines if item['group']=='5 AMVs' else 1
        assert item['quantity']==pytest.approx(rule['original_quantity']*multiplier)
        assert item['total']==money(rule['original_total']*multiplier)

@pytest.mark.parametrize('cfg',['Superfície','Elevado'])
def test_two_combined_budgets_reconcile_to_both_manual_workbooks(model,cfg):
    """Ponte independente de subtotais manuais; não é um terceiro orçamento original."""
    rules,catalog=model
    result=calculate(Scenario(configuration=cfg),rules,catalog)
    snapshots=json.loads((ROOT/'data/snapshots.json').read_text(encoding='utf-8'))
    rows=snapshots['vp'][cfg]['values']
    kept=[row for row in rows if len(row)>10 and isinstance(row[3],str) and row[3].startswith('SIEC-') and row[2]!='Topografia' and row[1]!='02 Drenagem' and row[2] not in ('Canaletas de cabos','Passa-fios','Conexões')]
    original_kept=money(sum(row[10] for row in kept))
    topo=63301.67 if cfg=='Superfície' else 148069.67 # Monitoramento 6 / 18 meses; demais itens gerais mantidos.
    drainage=1291857.60
    if cfg=='Elevado':drainage+=773871.23 # 2.000m canaletas + 51x8m descidas + 51 caixas.
    expected_direct=money(original_kept+topo+drainage+691300+829930.32)
    assert result['direct']==expected_direct
    for item in result['items']:
        if item['origin']=='vp':
            manual=rows[item['row']-1]
            assert item['quantity']==pytest.approx(manual[8])
            assert item['total']==manual[10]

def test_price_sources_and_duplicates(model):
    r,c=model
    assert len(c)==13260
    assert sum(x['source']=='SIEC' for x in c.values())==13176
    for row in c.values():
        if row['source']=='SIEC':assert len(json.loads(row['provenance']))==2
    assert len(json.loads((ROOT/'config/coverage.json').read_text(encoding='utf-8')))==281

def test_hierarchy_missing_price_and_unit(model):
    rules,c=copy.deepcopy(model)
    keys=['s','n','r','m']
    for k,source in zip(keys,['SIEC','SINAPI','SICRO','Mercado']):c[k]={'key':k,'code':k,'source':source,'price':10}
    assert resolve_price(list(reversed(keys)),c,rules['source_priority'])['source']=='SIEC'
    c['s']['price']=None
    assert resolve_price(keys,c,rules['source_priority'])['source']=='SINAPI'
    with pytest.raises(ValueError):resolve_price(['missing'],c,rules['source_priority'])
    used=calculate(Scenario(),rules,c)['items'][0]['price_key'];c[used]['unit']='incompatível'
    with pytest.raises(ValueError,match='Unidade'):calculate(Scenario(),rules,c)

@pytest.mark.parametrize('params',[{'km':0},{'km':float('nan')},{'amvs':-1},{'amvs':1.5},{'km':.04,'amvs':1},{'lines':3},{'bdi':-1},{'profile':'other'}])
def test_invalid_inputs(model,params):
    with pytest.raises(ValueError):calculate(Scenario(**params),*model)

@pytest.mark.parametrize('profile',['siec','legacy'])
def test_lengths_zero_amvs_and_optional_groups(model,profile):
    for km in [.01,.55,1.3,5]:
        result=calculate(Scenario(km=km,lines=2,amvs=0,profile=profile,ducts=False,topography=False,fence='Nenhuma'),*model)
        assert result['groups']['2 Topografia']==result['groups']['4 Vedação']==result['groups']['5 AMVs']==result['groups']['6 Banco de dutos']==0
        assert all(x['quantity']>=0 for x in result['items'])
        assert result['per_line_km']==money(result['total']/(2*km))
    a=calculate(Scenario(km=1,lines=2,amvs=1,profile=profile),*model)
    assert a['context']['sleepers']==(math.ceil(1000/.6)+math.ceil((1000-a['context']['envelope'])/.6))

def test_no_code_execution():
    for expr in ["__import__('os').system('echo bad')",'(1).__class__','[1][0]','2**1000000']:
        with pytest.raises(ValueError):evaluate(expr,{})

def test_monotonic_alternatives(model):
    totals=[calculate(Scenario(drainage=d),*model)['total'] for d in ['Normal','Reforçada','Complexa']]
    assert totals==sorted(totals)
    assert calculate(Scenario(fence='Muro'),*model)['total']>calculate(Scenario(),*model)['total']
