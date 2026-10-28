from dataclasses import replace

import pytest

from railbudget.engine import Scenario, load_model, select_groups
from railbudget.elevated import calculate_elevated
from railbudget.elevated_track import TRACK_COMPONENTS, track_breakdown, track_sensitivity


@pytest.fixture(scope='module')
def model():
    return load_model()


def full(result):
    return select_groups(result,list(result['groups']))


def test_via_permanente_soma_itens_existentes_sem_preco_novo(model):
    rules,catalog=model
    result=full(calculate_elevated(Scenario(configuration='Elevado',rolling_stock=False),rules,catalog))
    breakdown=track_breakdown(result)
    names=[row['Componente'] for row in breakdown['rows']]
    assert names==[name for name,_,_ in TRACK_COMPONENTS]
    by_name={row['Componente']:row['Custo direto (R$)'] for row in breakdown['rows']}
    # Conferência independente pelos rótulos e grupos dos itens do orçamento.
    rails=sum(item['total'] for item in result['items'] if item['label']=='Trilhos')
    amvs=next(value for group,value in result['groups'].items() if group.startswith('5 '))
    assert by_name['Trilhos']==pytest.approx(rails) and by_name['AMVs']==pytest.approx(amvs)
    assert all(value>0 for value in by_name.values())
    assert breakdown['direct']==pytest.approx(sum(by_name.values()),abs=.02)
    assert breakdown['direct']<result['direct']
    assert breakdown['per_viaduct_m']==pytest.approx(breakdown['direct']/1000,abs=.01)
    assert breakdown['with_bdi']==pytest.approx(breakdown['direct']*(1+result['scenario']['bdi']),abs=.02)
    assert sum(row['Participação (%)'] for row in breakdown['rows'])==pytest.approx(100)


def test_via_dupla_divide_por_km_de_via_e_respeita_grupos_marcados(model):
    rules,catalog=model
    result=calculate_elevated(Scenario(configuration='Elevado',rolling_stock=False,lines=2,km=2),rules,catalog)
    breakdown=track_breakdown(full(result))
    assert breakdown['track_km']==4 and breakdown['viaduct_m']==2000
    assert breakdown['per_track_km']==pytest.approx(breakdown['direct']/4,abs=.01)
    without_amv=track_breakdown(select_groups(result,[g for g in result['groups'] if not g.startswith('5 ')]))
    assert next(row for row in without_amv['rows'] if row['Componente']=='AMVs')['Custo direto (R$)']==0
    assert without_amv['direct']<breakdown['direct']


def test_sensibilidade_varre_vao_altura_tabuleiro_e_vias(model):
    rules,catalog=model
    p=Scenario(configuration='Elevado',rolling_stock=False)
    rows=track_sensitivity(p,rules,catalog)
    variables={row['Variável'] for row in rows}
    assert variables=={'Vão (m)','Altura dos pilares (m)','Tipologia do tabuleiro','Via'}
    spans=[row for row in rows if row['Variável']=='Vão (m)']
    assert len(spans)==8
    # Vão maior: menos apoios, estrutura por metro cai.
    assert spans[0]['Estrutura do viaduto (R$/m)']>spans[-1]['Estrutura do viaduto (R$/m)']
    heights=[row for row in rows if row['Variável']=='Altura dos pilares (m)']
    assert heights[0]['Estrutura do viaduto (R$/m)']<heights[-1]['Estrutura do viaduto (R$/m)']
    base=calculate_elevated(p,rules,catalog)
    point=next(row for row in spans if row['Valor']==20)
    assert point['Via permanente (R$/m)']==pytest.approx(track_breakdown(full(base))['per_viaduct_m'],abs=.01)
    decks=[row for row in rows if row['Variável']=='Tipologia do tabuleiro']
    assert len({row['Via permanente (R$/m)'] for row in decks})==1
    assert len({row['Estrutura do viaduto (R$/m)'] for row in decks})==5
    single,double=[row for row in rows if row['Variável']=='Via']
    assert double['Via permanente (R$/m)']>single['Via permanente (R$/m)']
    assert double['Via permanente (R$/km de via)']<single['Via permanente (R$/km de via)']


def test_sensibilidade_com_trechos_aplica_valor_a_todos_os_trechos(model):
    rules,catalog=model
    p=Scenario(configuration='Elevado',rolling_stock=False)
    segments=[
        {'Trecho':'A','Extensão (km)':.4,'Altura (m)':6,'Vão (m)':20,'Fundação':'Hélice contínua',
            'Diâmetro (m)':.8,'Profundidade (m)':18,'Estacas/apoio':4,'Interferência':'Baixa'},
        {'Trecho':'B','Extensão (km)':.6,'Altura (m)':14,'Vão (m)':30,'Fundação':'Estaca raiz',
            'Diâmetro (m)':.41,'Profundidade (m)':25,'Estacas/apoio':8,'Interferência':'Alta'}]
    rows=track_sensitivity(p,rules,catalog,segments)
    spans=[row for row in rows if row['Variável']=='Vão (m)']
    assert len(spans)==8 and spans[0]['Estrutura do viaduto (R$/m)']>spans[-1]['Estrutura do viaduto (R$/m)']
    # Um trecho único com valores próprios: a varredura parte desses valores.
    single=[{**segments[1],'Extensão (km)':1.0}]
    one=track_sensitivity(replace(p,elevated_segments=tuple(single)),rules,catalog)
    heights=[row for row in one if row['Variável']=='Altura dos pilares (m)']
    assert heights[0]['Estrutura do viaduto (R$/m)']<heights[-1]['Estrutura do viaduto (R$/m)']
