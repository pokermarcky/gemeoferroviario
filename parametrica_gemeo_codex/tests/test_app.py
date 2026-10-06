from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / 'app.py'


def test_capa_estatica_usa_trem_bidirecional_e_vias_distintas():
    scene=(APP.parent/'railbudget'/'static_scene_v2.py').read_text(encoding='utf-8')
    assert 'train-passenger-bidirectional-v2.webp' in scene
    assert '@keyframes' not in scene
    assert 'Pausar animação' not in scene
    assert all(track in scene for track in ('track slab','track ballast','track urban'))
    assert '.passenger img{height:88px;object-position:left bottom}' in scene
    assert '.passenger{left:0;' in scene
    assert '.cargo{left:53%;' in scene and 'transform:translateX(-50%)' in scene
    assert '.vlt{right:0;' in scene
    assert '.vlt img{object-position:right bottom}' in scene
    assert '_static_sprites_v3' in scene


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
    labels=[tab.label for tab in app.tabs]
    assert {'ORÇAMENTOS','Ferrovia de passageiro','Ferrovia de carga',
        'VLT - Veículo leve sobre Trilho','Shortline','BASES DE REFERÊNCIA',
        'SIEC','SINAPI','SIURB','SICRO'}.issubset(labels)
    assert any(h.value == 'Parametric Rails' for h in app.title)
    assert app.selectbox(key='main_profile').options == ['SIEC • lastro / AMV nº 14']
    assert app.selectbox(key='main_configuration').options == ['Superfície', 'Elevado', 'Subterrâneo']
    assert app.checkbox(key='main_grupo_5').label == 'Banco de dutos'
    assert not any(x.label == 'Prazo da obra (meses)' for x in app.number_input)
    assert [(x.key, x.proto.label) for x in app.get('download_button')] == [
        ('main_excel', 'Baixar orçamento em Excel'), ('cargo_excel', 'Baixar orçamento em Excel')]
    assert not any(x.key == 'main_prepare' for x in app.button)
    assert {x.key for x in app.button if x.label=='Atualizar orçamento'}=={
        'main_calculate','cargo_calculate'}
    assert {u.key for u in app.get('file_uploader')} == {
        'upload_SIEC_Serviços','upload_SINAPI_Insumos',
        'upload_SIURB_Insumos','upload_SICRO_Insumos'}
    assert all(set(u.proto.type) == {'.csv', '.xls', '.xlsx', '.xlsm'} for u in app.get('file_uploader'))
    source=APP.read_text(encoding='utf-8')
    assert "key=key+'_service_bulk'" in source
    assert "['Marcar todas','Desmarcar todas']" in source
    assert app.number_input(key='main_bdi_personalizado').value == 26.30
    assert app.number_input(key='cargo_bdi_personalizado').value == 26.30
    assert not any('Estações de passageiros' in x.label for x in app.expander)
    assert not any(x.key and x.key.startswith('main_station') for x in app.number_input)
    assert not any('Orçamento paramétrico em preparação' in x.value for x in app.info)


def test_subterraneo_calcula_composicao_propria_e_libera_excel():
    app = AppTest.from_file(str(APP)).run(timeout=30)
    app.selectbox(key='main_configuration').set_value('Subterrâneo').run(timeout=30)
    assert not app.exception
    assert not app.button(key='main_calculate').proto.disabled
    assert app.checkbox(key='main_grupo_3').label == 'Segurança e ventilação'
    assert not any(x.key=='main_fence' for x in app.selectbox)
    app.button(key='main_calculate').click().run(timeout=30)
    assert not app.exception
    result=app.session_state['results']['main']
    assert result['scenario']['configuration']=='Subterrâneo'
    assert result['model_label']=='SIEC • subterrâneo preliminar'
    assert any(x.key == 'main_excel' for x in app.get('download_button'))


def test_selecao_de_grupos_e_bdi_no_resultado():
    from railbudget.expressions import money
    from railbudget.exporters import currency

    app = AppTest.from_file(str(APP)).run(timeout=30)
    direct = app.session_state['results']['main']['direct']
    app.number_input(key='main_bdi_personalizado').set_value(25.0).run(timeout=30)
    assert app.metric[0].value == currency(money(direct + money(direct * .25)))
    app.checkbox(key='main_aplicar_bdi').uncheck().run(timeout=30)
    assert app.metric[0].value == currency(direct)
    app.checkbox(key='main_grupo_2').uncheck().run(timeout=30)
    assert app.metric[0].value != currency(direct)


def test_selecao_rapida_marca_e_desmarca_servicos():
    app=AppTest.from_file(str(APP)).run(timeout=30)
    bulk=next(x for x in app.get('button_group') if x.key=='main_service_bulk')
    bulk.set_value('Desmarcar todas').run(timeout=30)
    assert not any(app.checkbox(key=f'main_grupo_{index}').value for index in range(9))
    bulk=next(x for x in app.get('button_group') if x.key=='main_service_bulk')
    bulk.set_value('Marcar todas').run(timeout=30)
    assert all(app.checkbox(key=f'main_grupo_{index}').value for index in range(9))


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


def test_upload_siec_recalcula_orcamento_com_codigo_sem_prefixo():
    from railbudget.reference_data import parse_reference

    app=AppTest.from_file(str(APP)).run(timeout=30)
    original=app.session_state['results']['main']
    item=next(row for row in original['items'] if row['source']=='SIEC')
    new_price=item['unit_cost']*2
    code=item['code'].removeprefix('SIEC-')
    raw=(f'Código;Descrição;Unidade;Preço\n{code};Preço 07/26;{item["unit"]};{new_price}\n').encode()
    base=parse_reference(raw,'SIEC_07_26.csv','SIEC','Serviços','07/2026')
    app.session_state['reference_bases']={('SIEC','Serviços'):base}
    app.run(timeout=30)
    assert not app.exception
    updated=app.session_state['results']['main']
    updated_item=next(row for row in updated['items'] if row['id']==item['id'])
    assert updated_item['unit_cost']==new_price
    assert updated['total']!=original['total']


def test_detalhamento_exibe_apenas_grupos_selecionados():
    app=AppTest.from_file(str(APP)).run(timeout=30)
    for index in range(1,9):
        app.checkbox(key=f'main_grupo_{index}').uncheck()
    app.run(timeout=30)
    assert not app.exception
    # A única ocorrência remanescente de Drenagem pertence ao orçamento de carga.
    assert sum(x.value=='Drenagem' for x in app.subheader)==1
    assert sum(x.value=='Via permanente' for x in app.subheader)==2


def test_carga_orca_so_infraestrutura_com_siec():
    app=AppTest.from_file(str(APP)).run(timeout=30)
    assert app.checkbox(key='cargo_grupo_5').value is False
    assert app.checkbox(key='cargo_grupo_4').value is False
    assert app.checkbox(key='cargo_grupo_6').value is False
    assert app.checkbox(key='cargo_grupo_7').value is False
    app.number_input(key='cargo_locomotives').set_value(.34)
    app.number_input(key='cargo_wagons').set_value(.34).run(timeout=30)
    app.button(key='cargo_calculate').click().run(timeout=30)
    assert not app.exception
    cargo=app.session_state['results']['cargo']
    passenger=app.session_state['results']['main']
    assert cargo['total']<passenger['total']
    assert cargo['scenario']['rolling_stock'] is False
    assert '9 Material rodante' not in cargo['groups']
    assert all(x['source']=='SIEC' for x in cargo['items'])
    assert cargo['scenario']['locomotives']==.34
    assert cargo['scenario']['wagons']==.34
    assert any('0,34 vagão' in warning for warning in cargo['warnings'])
    assert {x.key for x in app.get('download_button')}=={'main_excel','cargo_excel'}
