"""Adaptação explícita da via de carga aos itens precificados na base SIEC."""

from collections import Counter
from .engine import calculate, money


def calculate_freight(scenario, axle_load, rules, catalog):
    """Orça infraestrutura de carga, mantendo os preços e unidades do catálogo.

    A base dispõe de trilhos TR57 e UIC60 precificados; o segundo é usado na
    alternativa de 25 t/eixo. Dimensionamento definitivo depende do projeto.
    """
    if axle_load not in (20, 25):
        raise ValueError('Selecione uma das alternativas de carga por eixo com itens SIEC precificados.')
    if scenario.configuration != 'Superfície' or scenario.rolling_stock:
        raise ValueError('O modelo preliminar de carga cobre apenas a infraestrutura em superfície.')
    result = calculate(scenario, rules, catalog)
    if axle_load == 25:
        replacements = {
            'vp:Superfície:26': ('SIEC-03.04.01.100.10', 60 / 57),
            'vp:Superfície:33': ('SIEC-03.03.04.100.03', 1),
        }
        for item in result['items']:
            if item['id'] not in replacements:
                continue
            code, factor = replacements[item['id']]
            price = next((row for row in catalog.values() if row['code'] == code
                          and row['source'] == 'SIEC' and row['price'] is not None), None)
            if price is None or price['unit'] != item['unit']:
                raise ValueError('Preço SIEC de carga indisponível ou com unidade incompatível: ' + code)
            item.update(code=code, source=price['source'], description=price['description'],
                        unit_cost=price['price'], price_key=price['key'], date=price['date'],
                        provenance=price['provenance'], quantity=item['quantity'] * factor)
            item['total'] = money(item['quantity'] * item['unit_cost'])
            item['note'] = 'Alternativa de carga com trilho UIC60; conferir carga por eixo em projeto.'
    result['scenario']['axle_load'] = axle_load
    result['model_label'] = f'SIEC • carga / {"UIC60" if axle_load == 25 else "TR57"} · premissa {axle_load} t/eixo'
    result['groups'] = {g: money(sum(i['total'] for i in result['items'] if i['group'] == g))
                        for g in rules['groups'] if not g.startswith('9 ')}
    result['direct'] = money(sum(result['groups'].values()))
    result['bdi_amount'] = money(result['direct'] * scenario.bdi)
    result['total'] = money(result['direct'] + result['bdi_amount'])
    result['per_km'] = money(result['total'] / scenario.km)
    result['per_line_km'] = money(result['total'] / (scenario.km * scenario.lines))
    result['counts'] = dict(Counter(i['source'] for i in result['items']))
    result['warnings'].append('A carga por eixo seleciona trilho TR57 (20 t) ou UIC60 (25 t) e sua montagem com preços SIEC. Capacidade estrutural, dormentes, lastro e plataforma exigem verificação de projeto; não são dimensionados automaticamente.')
    return result
