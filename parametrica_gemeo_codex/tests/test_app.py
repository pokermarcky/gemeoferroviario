from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / 'app.py'


def test_passageiro_calcula_siec_e_limpa_resultado_invalido():
    from railbudget.engine import Scenario, calculate, load_model

    app = AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.exception
    app.button(key='main_calculate').click().run(timeout=30)
    assert app.session_state['results']['main']['total'] == calculate(Scenario(), *load_model())['total']
    app.number_input(key='main_km').set_value(.01)
    app.button(key='main_calculate').click().run(timeout=30)
    assert app.error
    assert 'main' not in app.session_state['results']


def test_navegacao_e_controles_solicitados():
    app = AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.exception
    assert [tab.label for tab in app.tabs] == [
        'Ferrovia de passageiro', 'Resumo geral', 'Detalhamento por grupo',
        'Ferrovia de carga', 'VLT - Veículo leve sobre Trilho', 'Shortline']
    assert any(h.value == 'ORÇAMENTOS' for h in app.header)
    assert app.selectbox(key='main_profile').options == ['SIEC • lastro / AMV nº 14']
    assert app.selectbox(key='main_configuration').options == ['Superfície', 'Elevado', 'Subterrâneo']
    assert app.checkbox(key='main_grupo_5').label == 'Banco de dutos'
    assert not any(x.label == 'Prazo da obra (meses)' for x in app.number_input)
    assert [(x.key, x.proto.label) for x in app.get('download_button')] == [
        ('main_excel', 'Baixar orçamento em Excel')]
    assert not any(x.key == 'main_prepare' for x in app.button)


def test_subterraneo_nao_reaproveita_preco_de_superficie():
    app = AppTest.from_file(str(APP)).run(timeout=30)
    app.selectbox(key='main_configuration').set_value('Subterrâneo').run(timeout=30)
    assert not app.exception
    assert app.button(key='main_calculate').proto.disabled
    assert not app.metric
    assert not app.get('download_button')


def test_selecao_de_grupos_e_bdi_no_resultado():
    from railbudget.expressions import money
    from railbudget.exporters import currency

    app = AppTest.from_file(str(APP)).run(timeout=30)
    direct = app.session_state['results']['main']['direct']
    app.number_input(key='main_bdi_personalizado').set_value(25.0).run(timeout=30)
    assert app.metric[0].value == currency(money(direct + money(direct * .25)))
    app.checkbox(key='main_aplicar_bdi').uncheck().run(timeout=30)
    assert app.metric[0].value == currency(direct)
    app.button(key='main_desmarcar_todas').click().run(timeout=30)
    assert app.metric[0].value == 'R$ 0,00'
    assert not app.get('download_button')
    app.button(key='main_selecionar_todas').click().run(timeout=30)
    assert app.metric[0].value == currency(direct)
    assert len(app.get('download_button')) == 1


def test_banco_de_dutos_e_opcoes_do_grupo():
    app = AppTest.from_file(str(APP)).run(timeout=30)
    completo = app.metric[0].value
    app.checkbox(key='main_grupo_5').uncheck().run(timeout=30)
    assert not app.exception
    assert app.metric[0].value != completo
    app.checkbox(key='main_grupo_5').check().run(timeout=30)
    assert app.metric[0].value == completo
    app.selectbox(key='main_configuration').set_value('Elevado').run(timeout=30)
    assert app.checkbox(key='main_grupo_5').label == 'Canaletas e passa-fios'
    app.checkbox(key='main_grupo_3').uncheck().run(timeout=30)
    assert not any(x.key == 'main_fence' for x in app.selectbox)
