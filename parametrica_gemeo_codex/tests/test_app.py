from pathlib import Path
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/'app.py'

def test_streamlit_calculate_and_error_clear_stale_results():
    a=AppTest.from_file(str(APP)).run(timeout=30)
    assert not a.exception
    a.button(key='FormSubmitter:form_main-Calcular Orçamento').click().run(timeout=30)
    assert not a.exception
    assert a.session_state['results']['main']['total']==9929071.15
    a.number_input(key='main_km').set_value(.01)
    a.button(key='FormSubmitter:form_main-Calcular Orçamento').click().run(timeout=30)
    assert a.error
    assert 'main' not in a.session_state['results']

def test_streamlit_compare_and_base():
    a=AppTest.from_file(str(APP)).run(timeout=30)
    a.segmented_control(key='page').set_value('Comparar cenários').run(timeout=30)
    assert not a.exception
    a.button(key='FormSubmitter:form_A-Calcular Orçamento').click().run(timeout=30)
    a.button(key='FormSubmitter:form_B-Calcular Orçamento').click().run(timeout=30)
    assert not a.exception
    assert set(a.session_state['results'])=={'A','B'}
    assert len(a.metric)>=7
    a.segmented_control(key='page').set_value('Base de dados').run(timeout=30)
    a.text_input(key='base_search').set_value('SIEC-03.04.01.100.43').run(timeout=30)
    assert len(a.dataframe[0].value)==1
    assert not a.exception

def test_streamlit_exports():
    a=AppTest.from_file(str(APP)).run(timeout=30)
    a.button(key='FormSubmitter:form_main-Calcular Orçamento').click().run(timeout=30)
    a.button(key='main_prepare').click().run(timeout=60)
    assert not a.exception
    assert len(a.session_state['downloads']['main'])==4
