from io import BytesIO
import pytest
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from openpyxl import load_workbook
from docx import Document
from pypdf import PdfReader
from railbudget.engine import *
from railbudget.freight import calculate_freight
from railbudget.exporters import export_all

def test_export_values_formulas_and_documents():
    rules,catalog=load_model()
    result=calculate(Scenario(configuration='Elevado',lines=2,amvs=3,km=1.3,drainage='Complexa'),rules,catalog)
    files=export_all(result,catalog)
    with ZipFile(BytesIO(files['orcamento.xlsx'])) as package:
        assert package.testzip() is None
        assert package.read('[Content_Types].xml').startswith(b'<Types')
        worksheet_names=[name for name in package.namelist() if name.startswith('xl/worksheets/sheet') and name.endswith('.xml')]
        for name in worksheet_names:
            raw=package.read(name)
            ET.fromstring(raw)
            assert b'<ns0:worksheet' not in raw
        assert b'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"' in package.read('xl/worksheets/sheet2.xml')
    f=load_workbook(BytesIO(files['orcamento.xlsx']),data_only=False)
    v=load_workbook(BytesIO(files['orcamento.xlsx']),data_only=True)
    total_row=next(n for n in range(1,v['Resumo'].max_row+1) if v['Resumo'][f'A{n}'].value=='Total')
    assert v['Resumo'][f'B{total_row}'].value==result['total']
    assert len(f['Resumo']._charts)==1
    assert f['EAP']['H5'].value==result['items'][0]['unit_cost']
    assert all(sheet.freeze_panes is None for sheet in f.worksheets)
    assert f['Premissas']['A1'].value=='Premissas do cenário'
    assert f['Premissas']['B8'].value=='Quantidade de vias'
    assert not any('prazo' in str(cell.value).lower() for row in f['Premissas'].iter_rows() for cell in row if cell.value)
    assert 'fator de gestão (' in f['EAP']['L5'].value
    assert f['EAP']['M5'].value.startswith('Regra: Via permanente.')
    assert 'SIEC_INSUMOS' not in f.sheetnames
    reference_sheet=f['SIEC_SERVICOS']
    provenance=' '.join(str(cell.value or '') for cell in reference_sheet['G'][1:])
    assert 'aba ' in provenance and 'linha ' in provenance
    assert not any(term in provenance for term in ('"sheet"','"row"','"original_row"'))
    assert not any(cell.data_type=='f' for sheet in f.worksheets for row in sheet.iter_rows() for cell in row)
    assert not any('#REF!' in str(cell.value) for sheet in f.worksheets for row in sheet.iter_rows() for cell in row)
    for n,item in enumerate(result['items'],5):
        assert v['EAP'][f'I{n}'].value==item['total']
        assert v['EAP'][f'G{n}'].value==pytest.approx(item['quantity'])
    word=Document(BytesIO(files['relatorio.docx']))
    assert word.tables
    assert any('Memória de cálculo:' in paragraph.text for paragraph in word.paragraphs)
    for name in ['orcamento.pdf','relatorio.pdf']:
        doc=PdfReader(BytesIO(files[name]));assert len(doc.pages)>1
        text=''.join(page.extract_text() for page in doc.pages)
        assert all(item['code'] in text for item in result['items'])
        if name=='relatorio.pdf':assert 'Memória de cálculo:' in text


def test_excel_de_carga_explica_que_frota_nao_esta_precificada():
    rules,catalog=load_model()
    scenario=Scenario(rolling_stock=False,trainsets=0,overhead=False,signaling=False,amvs=0,ducts=False)
    result=calculate_freight(scenario,25,rules,catalog)
    result['scenario'].update(locomotives=.34,wagons=12.5)
    workbook=load_workbook(BytesIO(export_all(result,catalog)['orcamento.xlsx']),data_only=True)
    resumo={workbook['Resumo'][f'A{row}'].value:workbook['Resumo'][f'B{row}'].value
        for row in range(1,workbook['Resumo'].max_row+1)}
    assert resumo['Frota de carga']=='Não precificada no total'
    assert resumo['Locomotivas informadas (un/km)']==.34
    assert resumo['Vagões informados (un/km)']==12.5
    assert 'aquisição' in resumo['Observação']
    assert '9 Material rodante' not in workbook.sheetnames
