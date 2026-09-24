"""Estações de passageiros com quantitativos e preços fornecidos pelo usuário."""
from copy import deepcopy
from .expressions import money

STATION_GROUP = '10 Estações de passageiros'
STATION_SIZES = ('Pequena', 'Média', 'Grande')


def include_stations(result, stations):
    """Acrescenta verbas explícitas; jamais atribui um preço SIEC a uma estação inteira."""
    out = deepcopy(result)
    custom_prices = {}
    for index, size in enumerate(STATION_SIZES, 1):
        quantity, unit_cost = stations[size]
        if type(quantity) is not int or not 0 <= quantity <= 1000:
            raise ValueError('Quantidade de estações inválida: ' + size)
        if not isinstance(unit_cost, (int, float)) or not 0 <= unit_cost <= 1e12:
            raise ValueError('Preço unitário de estação inválido: ' + size)
        if quantity and not unit_cost:
            raise ValueError('Informe o preço unitário da estação ' + size.lower() + ' antes de calcular.')
        if not quantity:
            continue
        key = f'Usuário|Serviços|informada|EST-{index:02d}'
        custom_prices[key] = {'key': key, 'code': f'EST-{index:02d}',
            'description': 'Estação ' + size.lower() + ' — verba unitária informada pelo usuário',
            'unit': 'un', 'price': float(unit_cost), 'source': 'Usuário',
            'kind': 'Serviços', 'date': 'Informada pelo usuário',
            'provenance': 'Premissa inserida no formulário; confirmar projetos, escopo e data-base.'}
        out['items'].append({'id': f'estacao:{index}', 'eap': f'10.{index:03d}',
            'original_eap': f'10.{index:03d}', 'group': STATION_GROUP,
            'label': 'Estação ' + size.lower(), 'code': f'EST-{index:02d}',
            'source': 'Usuário', 'description': custom_prices[key]['description'],
            'unit': 'un', 'quantity': quantity, 'unit_cost': float(unit_cost),
            'total': money(quantity * unit_cost), 'price_key': key,
            'date': 'Informada pelo usuário', 'quantity_formula': str(quantity),
            'original_formula': str(quantity), 'note': 'Preço unitário informado pelo usuário.',
            'origin': 'Premissa do usuário', 'sheet': 'Estações', 'row': index,
            'provenance': custom_prices[key]['provenance']})
    if custom_prices:
        out['groups'][STATION_GROUP] = money(sum(x['total'] for x in out['items'] if x['group'] == STATION_GROUP))
        out['warnings'].append('Estações: preços unitários e quantidades informados pelo usuário, sem composição SIEC de edifício completo. Conferir escopo e data-base.')
    out['custom_prices'] = custom_prices
    return out
