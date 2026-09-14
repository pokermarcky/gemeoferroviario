from io import BytesIO
import pytest
from openpyxl import load_workbook
from docx import Document
from pypdf import PdfReader
from railbudget.engine import *
from railbudget.exporters import export_all

def test_export_values_formulas_and_documents():
    rules,catalog=load_model()
    result=calculate(Scenario(configuration='Elevado',lines=2,amvs=3,km=1.3,drainage='Complexa'),rules,catalog)
    files=export_all(result,catalog)
    f=load_workbook(BytesIO(files['orcamento.xlsx']),data_only=False)
    v=load_workbook(BytesIO(files['orcamento.xlsx']),data_only=True)
    assert v['Resumo']['B13'].value==result['total']
    assert len(f['Resumo']._charts)==1
    assert f['EAP']['H5'].value.startswith('=VLOOKUP(')
    assert f['EAP'].freeze_panes=='A5'
    for n,item in enumerate(result['items'],5):
        assert v['EAP'][f'I{n}'].value==item['total']
        assert v['EAP'][f'G{n}'].value==pytest.approx(item['quantity'])
    assert Document(BytesIO(files['relatorio.docx'])).tables
    for name in ['orcamento.pdf','relatorio.pdf']:
        doc=PdfReader(BytesIO(files[name]));assert len(doc.pages)>1
        text=''.join(page.extract_text() for page in doc.pages)
        assert all(item['code'] in text for item in result['items'])
