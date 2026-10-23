import pytest
from railbudget.engine import Scenario, load_model, calculate, select_groups
from railbudget.freight import calculate_freight


def test_freight_has_distinct_priced_track_and_reacts_to_axle_and_length():
    rules, catalog = load_model()
    passenger = calculate(Scenario(), rules, catalog)
    base = Scenario(rolling_stock=False, trainsets=0, overhead=False,
                    signaling=False, amvs=0, ducts=False)
    light = calculate_freight(base, 20, rules, catalog)
    heavy = calculate_freight(base, 25, rules, catalog)
    long = calculate_freight(Scenario(km=2, rolling_stock=False, trainsets=0,
                                      overhead=False, signaling=False, amvs=0, ducts=False),
                             25, rules, catalog)
    rail = next(i for i in heavy['items'] if i['id'] == 'vp:Superfície:26')
    assembly = next(i for i in heavy['items'] if i['id'] == 'vp:Superfície:33')
    assert rail['code'] == 'SIEC-03.04.01.100.10'
    assert rail['quantity'] == pytest.approx(2 * 1000 * 60 / 1000 * 1.02)
    assert assembly['code'] == 'SIEC-03.03.04.100.03'
    assert heavy['total'] > light['total']
    assert long['total'] > heavy['total']
    assert heavy['total'] < passenger['total']
    assert sum(i['total'] for i in heavy['items']) == heavy['direct']
    assert '9 Material rodante' not in heavy['groups']
    assert select_groups(heavy, list(heavy['groups']))['total'] == heavy['total']


FREIGHT = dict(rolling_stock=False, trainsets=0, overhead=False, signaling=False, ducts=False)


def _item(result, row):
    return next(i for i in result['items'] if i['id'] == f'vp:Superfície:{row}')


def test_20_t_reproduz_a_referencia_siec_de_superficie():
    rules, catalog = load_model()
    for lines, amvs in ((1, 0), (2, 3)):
        scenario = Scenario(km=2.5, lines=lines, amvs=amvs, **FREIGHT)
        base = calculate(scenario, rules, catalog)
        light = calculate_freight(scenario, 20, rules, catalog)
        assert light['freight']['class'] == 'TR57'
        assert light['direct'] == pytest.approx(base['direct'])
        assert [(i['code'], i['quantity']) for i in light['items']] == \
               [(i['code'], i['quantity']) for i in base['items']]


def test_25_t_troca_perfil_e_redimensiona_lastro_e_plataforma():
    rules, catalog = load_model()
    scenario = Scenario(km=2, lines=1, amvs=0, **FREIGHT)
    light = calculate_freight(scenario, 20, rules, catalog)
    heavy = calculate_freight(scenario, 25, rules, catalog)
    assert heavy['freight']['class'] == 'UIC60'
    assert _item(heavy, 27)['code'] == 'SIEC-03.04.01.100.03'
    assert _item(heavy, 36)['code'] == 'SIEC-03.03.04.100.32'
    assert heavy['freight']['premises']['ballast_depth'] == pytest.approx(.35)
    assert heavy['freight']['platform_width'] == pytest.approx(6.15)
    assert _item(heavy, 31)['quantity'] > _item(light, 31)['quantity']
    assert _item(heavy, 32)['quantity'] == pytest.approx(_item(heavy, 31)['quantity'] * 20)
    assert _item(heavy, 24)['quantity'] == pytest.approx(2000 * 6.15)
    assert _item(heavy, 25)['quantity'] == pytest.approx(2000 * 6.15 * .20)
    assert _item(heavy, 20)['quantity'] == pytest.approx(_item(light, 20)['quantity'] * 6.15 / 6)
    assert sum(i['total'] for i in heavy['items']) == pytest.approx(heavy['direct'])


def test_premissas_editaveis_redimensionam_dormentes_e_sublastro():
    rules, catalog = load_model()
    scenario = Scenario(km=1, lines=1, amvs=0, **FREIGHT)
    base = calculate_freight(scenario, 22.5, rules, catalog)
    dense = calculate_freight(scenario, 22.5, rules, catalog,
                              premises={'sleeper_spacing': .50, 'sublayer_thickness': .30})
    assert _item(base, 27)['quantity'] == 1667
    assert _item(dense, 27)['quantity'] == 2000
    assert _item(dense, 28)['quantity'] == 8000
    assert _item(dense, 30)['quantity'] == 4000
    assert _item(dense, 25)['quantity'] == pytest.approx(_item(base, 25)['quantity'] * 1.5)
    assert dense['scenario']['freight_premises']['sleeper_spacing'] == .50
    assert 'freight_sleepers' in _item(dense, 27)['quantity_formula']
    assert dense['total'] > base['total']


def test_carga_fora_da_faixa_precificada_e_bloqueada():
    rules, catalog = load_model()
    scenario = Scenario(**FREIGHT)
    with pytest.raises(ValueError, match='TR-68'):
        calculate_freight(scenario, 30, rules, catalog)
    with pytest.raises(ValueError, match='sleeper_spacing'):
        calculate_freight(scenario, 25, rules, catalog, premises={'sleeper_spacing': .9})


def test_patios_obras_de_arte_e_frota_ficam_listados_fora_do_total():
    rules, catalog = load_model()
    scenario = Scenario(**FREIGHT)
    plain = calculate_freight(scenario, 25, rules, catalog)
    listed = calculate_freight(scenario, 25, rules, catalog, pending={
        'locomotives': .5, 'wagons': 10, 'yards': 2, 'bridge_length': 120, 'level_crossings': 3})
    assert listed['total'] == plain['total']
    pending = {p['key']: p for p in listed['pending_scope']}
    assert pending['yards']['quantity'] == 2 and pending['bridge_length']['unit'] == 'm'
    assert all('fora do total' in p['status'] for p in listed['pending_scope'])
    assert listed['scenario']['bridge_length'] == 120
    assert any('pontes e viadutos' in w for w in listed['warnings'])


def test_orcamento_de_carga_salvo_antes_da_mudanca_reabre_com_a_geometria_original():
    import streamlit as st
    from railbudget.user_workspace import _load_budget_for_editing
    rules, catalog = load_model()
    saved = calculate_freight(Scenario(**FREIGHT), 25, rules, catalog)
    for name in ('freight_premises', 'axle_class', 'yards', 'bridge_length', 'level_crossings'):
        saved['scenario'].pop(name)
    saved['scenario']['axle_load'] = 25
    st.session_state.clear()
    _load_budget_for_editing({'id': '1', 'name': 'Antigo', 'modality': 'Ferrovia de carga'}, saved)
    assert st.session_state['cargo_axle'] == 25.0
    assert st.session_state['cargo_ballast_depth_UIC60'] == .30
    assert st.session_state['cargo_yards'] == 0
    assert st.session_state['cargo_calculated_inputs'][-1][1] == (.60, .30, .20)
