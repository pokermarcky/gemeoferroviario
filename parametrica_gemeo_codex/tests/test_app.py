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


def test_titulo_principal_centralizado_com_tipografia_moderna():
    theme=(APP.parent/'railbudget'/'interface.py').read_text(encoding='utf-8')
    assert '.st-key-hero h1' in theme
    assert 'margin-inline:auto;text-align:center' in theme
    assert '"Aptos Display","Segoe UI Variable Display","Segoe UI",Inter,system-ui,sans-serif' in theme


def test_carteira_de_projetos_tem_interface_amigavel():
    app = AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.exception
    source=(APP.parent/'railbudget'/'user_workspace.py').read_text(encoding='utf-8')
    assert '## Carteira de Projetos' in source
    assert 'key="budget_search"' in source
    assert '"Adicionar projeto"' in source
    assert 'Clique no nome de um projeto para abrir suas informações' in source
    assert '@st.dialog("Informações do projeto"' in source
    assert 'key=f"open_project_{budget_id}"' in source
    assert '"#### Dados técnicos"' in source
    assert '"Editar parâmetros e custos"' in source
    assert 'budget_edit_context' in source
    assert '"Salvar alteração"' in source
    assert 'Confirmo que desejo excluir este projeto' in source
    assert '"Ficha do projeto"' not in source
    assert 'Meus Orçamentos' not in source


def test_projeto_vlt_salvo_pode_ser_reaberto_recalculado_e_atualizado(monkeypatch,tmp_path):
    monkeypatch.setenv('RAILPARAMETRIC_BUDGET_DB',str(tmp_path/'budgets.sqlite3'))
    app=AppTest.from_file(str(APP)).run(timeout=30)
    open_project=next(button for button in app.button
        if button.key and button.key.startswith('open_project_'))
    app=open_project.click().run(timeout=30)
    load_project=next(button for button in app.button
        if button.key and button.key.startswith('load_budget_'))
    app=load_project.click().run(timeout=30)
    assert not app.exception
    assert app.session_state['budget_edit_context']['key']=='vlt'
    assert app.number_input(key='vlt_surface_km').value==.9
    app.number_input(key='vlt_surface_km').set_value(1.2).run(timeout=30)
    assert app.button(key='save_project_changes_vlt').disabled
    app.button(key='vlt_calculate').click().run(timeout=30)
    assert not app.button(key='save_project_changes_vlt').disabled
    app.button(key='save_project_changes_vlt').click().run(timeout=30)
    assert not app.exception
    assert 'budget_edit_context' not in app.session_state

    from railbudget.auth import UserContext
    from railbudget.budget_store import list_budgets
    root=UserContext('test-suite-root','root@test.invalid','Testes','root','test-suite')
    saved=list_budgets(root.user_id,root)
    assert saved[0]['result_json']['scenario']['surface_km']==1.2


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
    documents=[('excel','Excel'),('pdf_resumo','PDF resumido'),('pdf_detalhado','PDF detalhado'),('word','Word')]
    assert [(x.key, x.proto.label) for x in app.get('download_button')] == [
        *[('main_'+k,label) for k,label in documents],*[('cargo_'+k,label) for k,label in documents],
        ('vlt_excel','Baixar orçamento em Excel'),*[('shortline_'+k,label) for k,label in documents]]
    assert not any(x.key == 'main_prepare' for x in app.button)
    assert {x.key for x in app.button if x.label=='Atualizar orçamento'}=={
        'main_calculate','cargo_calculate','vlt_calculate','shortline_calculate'}
    assert {u.key for u in app.get('file_uploader')} == {
        'upload_SIEC_Serviços','upload_SINAPI_Insumos',
        'upload_SIURB_Insumos','upload_SICRO_Insumos'}
    assert all(set(u.proto.type) == {'.csv', '.xls', '.xlsx', '.xlsm'} for u in app.get('file_uploader'))
    source=APP.read_text(encoding='utf-8')
    assert '"Salvar alterações no projeto"' in source
    assert 'render_project_save_action' in source
    assert "key=key+'_service_bulk'" in source
    assert "['Marcar todas','Desmarcar todas']" in source
    assert app.number_input(key='main_bdi_personalizado').value == 26.30
    assert app.number_input(key='cargo_bdi_personalizado').value == 26.30
    assert not any('Estações de passageiros' in x.label for x in app.expander)
    assert not any(x.key and x.key.startswith('main_station') for x in app.number_input)
    assert not any('Orçamento paramétrico em preparação' in x.value for x in app.info)
    assert app.number_input(key='vlt_surface_km').value==.9
    assert app.number_input(key='vlt_elevated_km').value==1.7
    assert app.session_state['results']['vlt']['total']==191008605.92


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


def test_elevado_de_passageiros_tem_controles_estruturais_e_recalcula():
    app=AppTest.from_file(str(APP)).run(timeout=30)
    app.selectbox(key='main_configuration').set_value('Elevado').run(timeout=30)
    assert app.number_input(key='main_elevated_height').value==8.0
    assert app.number_input(key='main_elevated_span').value==20.0
    assert app.number_input(key='main_elevated_width_single').value==7.0
    assert app.number_input(key='main_elevated_width_double').value==11.0
    assert app.selectbox(key='main_elevated_foundation_type').options==['Hélice contínua','Estaca raiz']
    app.number_input(key='main_elevated_height').set_value(12.0)
    app.number_input(key='main_elevated_span').set_value(25.0)
    app.number_input(key='main_elevated_width_single').set_value(8.0)
    app.selectbox(key='main_elevated_urban_interference').set_value('Alta')
    app.selectbox(key='main_elevated_foundation_type').set_value('Estaca raiz').run(timeout=30)
    app.selectbox(key='main_elevated_pile_diameter_raiz').set_value(.41)
    app.number_input(key='main_elevated_foundation_depth').set_value(24.0)
    app.number_input(key='main_elevated_piles_per_support').set_value(6)
    app.button(key='main_calculate').click().run(timeout=30)
    assert not app.exception
    result=app.session_state['results']['main']
    assert result['scenario']['configuration']=='Elevado'
    assert result['scenario']['foundation_type']=='Estaca raiz'
    assert result['elevated']['supports']==41
    assert result['elevated']['total_piles']==246
    assert result['elevated']['active_width']==8


def test_elevado_avancado_organiza_solucoes_em_paineis_recolhiveis():
    app=AppTest.from_file(str(APP)).run(timeout=30)
    app.selectbox(key='main_configuration').set_value('Elevado').run(timeout=30)
    labels={item.label for item in app.expander}
    assert {'Fundações e condição urbana','Dividir o corredor em trechos homogêneos',
        'Soluções estruturais e método executivo','Obras singulares e proteção acústica'}.issubset(labels)
    assert app.selectbox(key='main_elevated_deck_type').options[0]=='Vigas pré-moldadas com laje'
    assert app.selectbox(key='main_elevated_pier_type').options[-1]=='Pórtico'
    app.selectbox(key='main_elevated_deck_type').set_value('Viga-caixão pré-moldada segmental')
    app.selectbox(key='main_elevated_pier_type').set_value('Pórtico')
    app.number_input(key='main_elevated_transitions').set_value(2)
    app.button(key='main_calculate').click().run(timeout=30)
    assert not app.exception
    result=app.session_state['results']['main']
    assert result['scenario']['deck_type']=='Viga-caixão pré-moldada segmental'
    assert result['scenario']['pier_type']=='Pórtico'
    assert result['scenario']['transitions']==2
    assert result['elevated']['indicators']['Custo por apoio']>0
    assert app.button(key='main_sensitivity_button')


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
    # As ocorrências remanescentes de Drenagem pertencem aos orçamentos de carga e shortline.
    assert sum(x.value=='Drenagem' for x in app.subheader)==2
    assert sum(x.value=='Via permanente' for x in app.subheader)==3


def test_carga_orca_so_infraestrutura_com_siec():
    app=AppTest.from_file(str(APP)).run(timeout=30)
    assert app.checkbox(key='cargo_grupo_5').value is False
    assert app.checkbox(key='cargo_grupo_4').value is False
    assert app.checkbox(key='cargo_grupo_6').value is False
    assert app.checkbox(key='cargo_grupo_7').value is False
    app.number_input(key='cargo_locomotives').set_value(.34)
    app.number_input(key='cargo_wagons').set_value(.34)
    app.number_input(key='cargo_yards').set_value(2)
    app.number_input(key='cargo_bridge_length').set_value(150.0)
    app.number_input(key='cargo_axle').set_value(22.5).run(timeout=30)
    app.number_input(key='cargo_ballast_depth_UIC60').set_value(.40).run(timeout=30)
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
    assert cargo['scenario']['axle_load']==22.5
    assert cargo['scenario']['freight_premises']['ballast_depth']==.40
    assert {p['key']:p['quantity'] for p in cargo['pending_scope']}['bridge_length']==150
    assert cargo['scenario']['yards']==2
    assert {x.key for x in app.get('download_button')}=={'vlt_excel',*(f'{tab}_{k}' for tab in ('main','cargo','shortline')
        for k in ('excel','pdf_resumo','pdf_detalhado','word'))}


def test_shortline_calcula_salva_e_reabre_para_edicao(monkeypatch,tmp_path):
    monkeypatch.setenv('RAILPARAMETRIC_BUDGET_DB',str(tmp_path/'budgets.sqlite3'))
    app=AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.exception
    shortline=app.session_state['results']['shortline']
    assert shortline['scenario']['modality']=='shortline'
    assert app.checkbox(key='shortline_grupo_6').value is False
    assert app.checkbox(key='shortline_grupo_1').label=='Desvios e pátios'
    app.number_input(key='shortline_km').set_value(25.0)
    app.number_input(key='shortline_level_crossings').set_value(6).run(timeout=30)
    assert any('Atualizar orçamento' in x.value for x in app.info)
    app.button(key='shortline_calculate').click().run(timeout=30)
    assert not app.exception
    result=app.session_state['results']['shortline']
    assert result['scenario']['km']==25.0 and result['scenario']['level_crossings']==6
    assert result['total']>shortline['total']
    from railbudget.auth import UserContext
    from railbudget.budget_store import list_budgets, save_budget
    from railbudget.user_workspace import MODALITY_LABELS
    root=UserContext('test-suite-root','root@test.invalid','Testes','root','test-suite')
    save_budget(root,'Shortline teste',MODALITY_LABELS['shortline'],app.session_state['display_results']['shortline'])
    app=AppTest.from_file(str(APP)).run(timeout=30)
    saved=next(row for row in list_budgets(root.user_id,root) if row['name']=='Shortline teste')
    app=next(b for b in app.button if b.key==f"open_project_{saved['id']}").click().run(timeout=30)
    app=next(b for b in app.button if b.key==f"load_budget_{saved['id']}").click().run(timeout=30)
    assert not app.exception
    assert app.session_state['budget_edit_context']['key']=='shortline'
    assert app.number_input(key='shortline_km').value==25.0
    assert app.number_input(key='shortline_level_crossings').value==6
    assert not any('Atualizar orçamento' in x.value for x in app.info if 'alterou' in x.value)


def test_demonstracao_tem_um_unico_download_em_qualquer_formato_inclusive_vlt(monkeypatch):
    import time
    monkeypatch.delenv('RAILPARAMETRIC_TEST_MODE')
    app=AppTest.from_file(str(APP))
    app.session_state['local_auth']={'role':'test','issued_at':time.time()}
    app.run(timeout=60)
    assert not app.exception
    keys={x.key for x in app.get('download_button')}
    assert {'main_excel','main_pdf_resumo','main_pdf_detalhado','main_word','vlt_excel'}<=keys
    app.session_state['trial_excel_downloads']=1
    app.run(timeout=60)
    assert not app.exception
    assert not app.get('download_button')
    assert any('download de demonstração já foi utilizado' in x.value for x in app.info)
    source=APP.read_text(encoding='utf-8')
    assert "key='vlt_excel',icon=':material/download:',on_click=register_trial_download" in source


def test_resumo_mostra_so_grupos_marcados_bdi_com_duas_casas_e_shortline_desatualizada():
    app=AppTest.from_file(str(APP)).run(timeout=60)
    assert not app.exception
    assert any('BDI aplicado: 26,30%' in x.value for x in app.caption)
    assert not any('26,300000' in x.value for x in app.caption)
    cargo_tables=[t.value for t in app.dataframe if 'Participação' in t.value.columns]
    assert cargo_tables and all(len(t)>0 for t in cargo_tables)
    groups=[set(t['Grupo']) for t in cargo_tables]
    assert any('Rede aérea' not in g and 'Via permanente' in g for g in groups)  # carga: desmarcados ficam fora
    assert "sort='-x'" in APP.read_text(encoding='utf-8')  # gráfico do maior para o menor
    app.number_input(key='shortline_km').set_value(20.0).run(timeout=60)
    assert any('alterou o cenário' in x.value for x in app.info)
    assert any(x.key=='shortline_excel' for x in app.get('download_button'))  # resultado anterior continua visível
