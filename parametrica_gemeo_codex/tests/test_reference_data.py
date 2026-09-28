from railbudget.engine import load_model
from railbudget.reference_data import parse_reference, apply_reference_bases


def test_uploaded_base_replaces_linked_price_and_keeps_only_current_slot():
    _, catalog = load_model()
    target = next(item for item in catalog.values()
                  if item['source'] == 'SIEC' and item['kind'] == 'Serviços' and item['price'])
    csv = ('Código;Descrição;Unidade;Preço\n'
           f'{target["code"]};Preço atualizado;{target["unit"]};4.079.193,32\n').encode()
    base = parse_reference(csv, 'siec-08-2026.csv', 'SIEC', 'Serviços', '08/2026')
    updated, linked = apply_reference_bases(catalog, {('SIEC', 'Serviços'): base})
    assert linked[('SIEC', 'Serviços')] >= 1
    assert updated[target['key']]['price'] == 4079193.32
    assert updated[target['key']]['date'] == '08/2026'


def test_reference_requires_pricing_columns():
    try:
        parse_reference(b'codigo;texto\n1;sem preco\n', 'base.csv', 'SINAPI', 'Insumos', '08/2026')
    except ValueError as exc:
        assert 'Colunas obrigatórias' in str(exc)
    else:
        raise AssertionError('A tabela incompleta deveria ser rejeitada.')
