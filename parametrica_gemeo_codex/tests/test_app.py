from pathlib import Path
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/'app.py'

def test_streamlit_calculate_and_error_clear_stale_results():
    from railbudget.engine import Scenario,calculate,load_model
    a=AppTest.from_file(str(APP)).run(timeout=30)
    assert not a.exception
    a.button(key='main_calculate').click().run(timeout=30)
    assert not a.exception
    assert a.session_state['results']['main']['total']==calculate(Scenario(),*load_model())['total']
    a.number_input(key='main_km').set_value(.01)
    a.button(key='main_calculate').click().run(timeout=30)
    assert a.error
    assert 'main' not in a.session_state['results']

def test_streamlit_compare_and_base():
    a=AppTest.from_file(str(APP)).run(timeout=30)
    a.segmented_control(key='page').set_value('Comparar cenários').run(timeout=30)
    assert not a.exception
    a.button(key='A_calculate').click().run(timeout=30)
    a.button(key='B_calculate').click().run(timeout=30)
    assert not a.exception
    assert {'A','B'}<=set(a.session_state['results'])
    assert len(a.metric)>=7
    a.segmented_control(key='page').set_value('Base de dados').run(timeout=30)
    a.text_input(key='base_search').set_value('SIEC-03.04.01.100.43').run(timeout=30)
    assert len(a.dataframe[0].value)==1
    assert not a.exception

def test_streamlit_exports():
    from io import BytesIO
    from zipfile import ZipFile
    a=AppTest.from_file(str(APP)).run(timeout=30)
    a.button(key='main_calculate').click().run(timeout=30)
    a.button(key='main_prepare').click().run(timeout=60)
    assert not a.exception
    assert len(a.session_state['downloads']['main'])==4
    for name in ('orcamento.xlsx','relatorio.docx'):
        with ZipFile(BytesIO(a.session_state['downloads']['main'][name])) as archive:
            text=' '.join(archive.read(member).decode('utf-8','ignore') for member in archive.namelist())
        assert 'C:\\Users\\' not in text
        assert 'marce' not in text.lower()
        assert 'sis.cptm.sp.gov.br' not in text.lower()
        assert 'file://' not in text.lower()


def test_live_scope_selection_and_stale_downloads():
    a=AppTest.from_file(str(APP)).run(timeout=30)
    a.button(key='main_calculate').click().run(timeout=30)
    a.button(key='main_prepare').click().run(timeout=60)
    for i in (0,1,2,4,5,6,7,8):a.checkbox(key=f'main_grupo_{i}').uncheck()
    a.run(timeout=30)
    assert not a.exception
    assert 'main' not in a.session_state['downloads']
    assert a.metric[0].value=='R$ 883.770,56'
    a.segmented_control(key='page').set_value('Base de dados').run(timeout=30)
    a.segmented_control(key='page').set_value('Orçamento').run(timeout=30)
    assert not a.checkbox(key='main_grupo_0').value
    assert a.metric[0].value=='R$ 883.770,56'
    a.checkbox(key='main_grupo_3').uncheck().run(timeout=30)
    assert not a.exception
    assert a.metric[0].value=='R$ 0,00'
    assert not any(b.key=='main_prepare' for b in a.button)


def test_scope_is_independent_in_comparison():
    a=AppTest.from_file(str(APP)).run(timeout=30)
    a.segmented_control(key='page').set_value('Comparar cenários').run(timeout=30)
    a.button(key='A_calculate').click().run(timeout=30)
    a.button(key='B_calculate').click().run(timeout=30)
    old_b=a.metric[2].value
    for i in range(9):a.checkbox(key=f'A_grupo_{i}').uncheck()
    a.run(timeout=30)
    assert not a.exception
    assert a.metric[0].value=='R$ 0,00'
    assert a.metric[2].value==old_b


def test_initial_screen_has_clear_summary_and_group_detail():
    a=AppTest.from_file(str(APP)).run(timeout=30)
    assert not a.exception
    assert [t.label for t in a.tabs]==['Resumo geral','Detalhamento por grupo']
    headings=[h.value for h in a.subheader]
    for name in ['Via permanente','Topografia','Drenagem','Vedação','AMVs','Infraestrutura de cabos','Rede aérea','Sinalização','Material rodante','EAP orçada']:
        assert name in headings
    sidebar_labels=[x.label for x in a.checkbox if x.key and (x.key.startswith('main_') and '_grupo_' not in x.key)]
    assert 'Incluir banco de seis dutos' not in sidebar_labels
    assert 'Incluir topografia' not in sidebar_labels
    assert not any(h.value=='Defina o cenário' for h in a.header)
    assert a.selectbox(key='main_fence').label=='Tipo de vedação'


def test_group_options_open_only_when_selected():
    a=AppTest.from_file(str(APP)).run(timeout=30)
    assert a.selectbox(key='main_fence').value=='Cerca'
    a.checkbox(key='main_grupo_3').uncheck().run(timeout=30)
    assert not any(x.key=='main_fence' for x in a.selectbox)
    a.checkbox(key='main_grupo_3').check().run(timeout=30)
    a.selectbox(key='main_fence').set_value('Muro')
    a.button(key='main_calculate').click().run(timeout=30)
    assert a.session_state['results']['main']['scenario']['fence']=='Muro'


def test_custom_bdi_updates_immediately_and_can_be_disabled():
    from railbudget.expressions import money
    from railbudget.exporters import currency
    from openpyxl import load_workbook
    from io import BytesIO
    a=AppTest.from_file(str(APP)).run(timeout=30)
    direct=a.session_state['results']['main']['direct']
    a.number_input(key='main_bdi_personalizado').set_value(25.0).run(timeout=30)
    assert not a.exception
    assert a.metric[0].value==currency(money(direct+money(direct*.25)))

    a.button(key='main_prepare').click().run(timeout=60)
    values=load_workbook(BytesIO(a.session_state['downloads']['main']['orcamento.xlsx']),data_only=True)
    rows={values['Resumo'][f'A{n}'].value:n for n in range(1,values['Resumo'].max_row+1)}
    assert values['Resumo'][f'B{rows["BDI"]}'].value==.25
    assert values['Resumo'][f'B{rows["Total"]}'].value==money(direct+money(direct*.25))
    a.checkbox(key='main_aplicar_bdi').uncheck().run(timeout=30)
    assert not a.exception
    assert a.metric[0].value==currency(direct)
    assert a.metric[0].label=='Total sem BDI'
    assert 'main' not in a.session_state['downloads']
    a.checkbox(key='main_aplicar_bdi').check().run(timeout=30)
    assert a.number_input(key='main_bdi_personalizado').value==25.0
    assert a.metric[0].value==currency(money(direct+money(direct*.25)))


def test_select_and_clear_all_preserves_bdi():
    a=AppTest.from_file(str(APP)).run(timeout=30)
    a.number_input(key='main_bdi_personalizado').set_value(25.0).run(timeout=30)
    original=a.metric[0].value
    a.button(key='main_desmarcar_todas').click().run(timeout=30)
    assert not a.exception
    assert a.metric[0].value=='R$ 0,00'
    assert all(not a.checkbox(key=f'main_grupo_{i}').value for i in range(9))
    assert a.number_input(key='main_bdi_personalizado').value==25.0
    assert a.checkbox(key='main_aplicar_bdi').value
    a.button(key='main_selecionar_todas').click().run(timeout=30)
    assert not a.exception
    assert a.metric[0].value==original
    assert all(a.checkbox(key=f'main_grupo_{i}').value for i in range(9))
