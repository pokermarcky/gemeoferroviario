"""Orçamento paramétrico de shortline: ferrovia de carga curta em via singela.

O módulo reaproveita o motor de carga em superfície (``calculate_freight``) sem
alterá-lo. Acrescenta a via de desvios de cruzamento e de pátio com as mesmas
composições SIEC da via corrida e registra, fora do total, os itens de escopo
que a base não precifica (passagens em nível, frota, terminais e obras de arte).
Nenhum preço é criado aqui: todo valor do total vem do catálogo ativo.
"""
from collections import Counter
from dataclasses import dataclass, fields, replace
import math

from .engine import Scenario
from .expressions import money
from .freight import PENDING_FIELDS, calculate_freight
from .localization import IDENTIFICADOR

SIDING_GROUP = '1.3 Desvios e pátios'
# Grupos da base que fazem sentido numa shortline diesel em via singela.
# Banco de dutos, rede aérea e material rodante ficam de fora do modelo.
SHORTLINE_GROUPS = ('1 Via permanente', SIDING_GROUP, '2 Topografia', '3 Drenagem',
                    '4 Vedação', '5 AMVs', '8 Sinalização')
# Itens da via permanente que acompanham a extensão de via. Os itens anteriores
# (canteiro, sondagens, mobilização e administração local) já estão na linha
# principal e não são duplicados para a via de desvios e pátio.
FIRST_TRACK_ROW = 19
AMVS_PER_SIDING = 2
RULE_VERSION = 'SHORTLINE-1'


@dataclass(frozen=True)
class ShortlineParams:
    km: float = 10.0
    sidings: int = 1
    siding_length: float = 1000.0
    yard_length: float = 1500.0
    yard_amvs: int = 2
    axle_load: float = 25.0
    drainage: str = 'Normal'
    fence: str = 'Cerca'
    detection: str = 'Contador de eixos'
    level_crossings: int = 0
    locomotives: int = 0
    wagons: int = 0


FIELDS = tuple(f.name for f in fields(ShortlineParams))


def total_amvs(params):
    return AMVS_PER_SIDING * params.sidings + params.yard_amvs


def extra_track_km(params):
    return (params.sidings * params.siding_length + params.yard_length) / 1000


def validate_shortline(p):
    def whole(value, minimum, maximum, name):
        if type(value) is not int or not minimum <= value <= maximum:
            raise ValueError(f'{name} deve ser inteiro entre {minimum} e {maximum}.')

    def real(value, minimum, maximum, name):
        if not isinstance(value, (int, float)) or not math.isfinite(value) or not minimum <= value <= maximum:
            raise ValueError(f'{name} deve estar entre {minimum} e {maximum}.')

    real(p.km, 0.01, 10000, 'Extensão da linha principal (km)')
    whole(p.sidings, 0, 500, 'Quantidade de desvios de cruzamento')
    real(p.siding_length, 0, 10000, 'Comprimento útil por desvio (m)')
    real(p.yard_length, 0, 100000, 'Extensão de vias de pátio (m)')
    whole(p.yard_amvs, 0, 1000, 'AMVs de pátio')
    whole(p.level_crossings, 0, 10000, 'Passagens em nível')
    whole(p.locomotives, 0, 10000, 'Locomotivas')
    whole(p.wagons, 0, 100000, 'Vagões')
    if p.sidings and p.siding_length <= 0:
        raise ValueError('Informe o comprimento útil dos desvios de cruzamento.')
    if 0 < extra_track_km(p) < 0.01:
        raise ValueError('A via de desvios e pátio deve somar ao menos 10 m, ou zero.')


def _siding_items(params, rules, catalog, bdi):
    """Via adicional de desvios e pátio com as composições SIEC da via corrida."""
    km = extra_track_km(params)
    if not km:
        return [], {}
    scenario = Scenario(km=km, lines=1, drainage=params.drainage, fence='Nenhuma', amvs=0,
                        ducts=False, topography=False, overhead=False, signaling=False,
                        detection=params.detection, rolling_stock=False, trainsets=0, bdi=bdi)
    siding = calculate_freight(scenario, params.axle_load, rules, catalog)
    context = siding['context']
    renamed = {}

    def prefix(match):
        name = match.group()
        if name in context:
            renamed['patio_' + name] = context[name]
            return 'patio_' + name
        return name

    items = []
    for item in siding['items']:
        if item['group'] != '1 Via permanente' or item['row'] < FIRST_TRACK_ROW:
            continue
        copy = dict(item)
        copy.update(id='sl:patio:' + item['id'], group=SIDING_GROUP,
                    quantity_formula=IDENTIFICADOR.sub(prefix, item['quantity_formula']),
                    note=('Via de desvios de cruzamento e pátio, com a mesma composição SIEC da via '
                          'corrida. ' + item['note']).strip())
        items.append(copy)
    for sequence, item in enumerate(items, 1):
        item['eap'] = '1.3.' + str(sequence).zfill(3)
    return items, renamed


def calculate_shortline(params, rules, catalog, bdi=0.263):
    """Função pura: linha principal + desvios e pátio, com escopo pendente fora do total."""
    validate_shortline(params)
    if not math.isfinite(bdi) or not 0 <= bdi <= 1:
        raise ValueError('BDI deve estar entre 0% e 100%.')
    amvs = total_amvs(params)
    main_scenario = Scenario(km=params.km, lines=1, drainage=params.drainage, fence=params.fence,
                             amvs=amvs, ducts=False, topography=True, overhead=False, signaling=True,
                             detection=params.detection, rolling_stock=False, trainsets=0, bdi=bdi)
    result = calculate_freight(main_scenario, params.axle_load, rules, catalog)
    siding_items, siding_context = _siding_items(params, rules, catalog, bdi)
    items = [i for i in result['items'] if i['group'] in SHORTLINE_GROUPS] + siding_items
    items.sort(key=lambda i: SHORTLINE_GROUPS.index(i['group']))
    groups = {g: money(sum(i['total'] for i in items if i['group'] == g)) for g in SHORTLINE_GROUPS}
    direct = money(sum(groups.values()))
    bdi_amount = money(direct * bdi)
    total = money(direct + bdi_amount)
    track_km = params.km + extra_track_km(params)
    rail = result['freight']['rail']
    for name, *_ in PENDING_FIELDS:
        result['scenario'].pop(name, None)  # escopo da carga em un/km; a shortline registra o seu abaixo
    result['scenario'].update(modality='shortline', axle_load=params.axle_load, sidings=params.sidings,
        siding_length=params.siding_length, yard_length=params.yard_length, yard_amvs=params.yard_amvs,
        extra_track_km=extra_track_km(params), track_km=track_km, level_crossings=params.level_crossings,
        fleet_locomotives=params.locomotives, fleet_wagons=params.wagons)
    status = 'Não precificado · fora do total'
    pending = [
        {'key': 'level_crossings', 'item': 'Passagens em nível', 'quantity': float(params.level_crossings), 'unit': 'un',
         'status': status, 'reason': 'A SIEC não traz composição completa de passagem em nível rodoferroviária; tipo de proteção e pavimento dependem da via cruzada.'},
        {'key': 'fleet_locomotives', 'item': 'Locomotivas', 'quantity': float(params.locomotives), 'unit': 'un',
         'status': status, 'reason': 'A SIEC tem custo horário de operação, não preço de aquisição.'},
        {'key': 'fleet_wagons', 'item': 'Vagões', 'quantity': float(params.wagons), 'unit': 'un',
         'status': status, 'reason': 'A SIEC tem custo horário de operação, não preço de aquisição.'},
        {'key': 'terminals', 'item': 'Terminais de carga e descarga', 'quantity': 0.0, 'unit': 'a definir',
         'status': status, 'reason': 'Depende do produto, do arranjo e dos equipamentos do terminal.'},
        {'key': 'bridges', 'item': 'Pontes, viadutos e obras de arte especiais', 'quantity': 0.0, 'unit': 'a definir',
         'status': status, 'reason': 'Dependem do traçado e de projeto estrutural.'},
    ]
    warnings = list(result['warnings'])
    warnings += [
        'Shortline: via singela em superfície, tração diesel; banco de dutos, rede aérea e material rodante não fazem parte do modelo.',
        f'Desvios e pátio: {params.sidings} desvio(s) de {params.siding_length:.0f} m e {params.yard_length:.0f} m de vias de pátio, '
        'orçados com as composições SIEC da via corrida. Canteiro, sondagens e administração local não são duplicados; '
        'drenagem, vedação e topografia acompanham apenas a linha principal. Premissa a validar em projeto.',
        f'AMVs: {AMVS_PER_SIDING} por desvio de cruzamento + {params.yard_amvs} de pátio = {amvs} AMV(s) nº 14 da referência SIEC; '
        'abertura, número do AMV e leiaute de pátio exigem projeto geométrico.',
        'Sinalização é opcional na shortline; quando incluída, cobre apenas a linha principal.',
        'Fora do total: ' + br_list(pending) + '.',
    ]
    return {**result,
        'model_label': f'SIEC • shortline / {rail} · premissa {params.axle_load:g} t/eixo',
        'items': items, 'groups': groups, 'direct': direct, 'bdi_amount': bdi_amount, 'total': total,
        'per_km': money(total / params.km), 'per_line_km': money(total / params.km),
        'per_track_km': money(total / track_km),
        'counts': dict(Counter(i['source'] for i in items)), 'warnings': warnings,
        'rule_version': rules['version'] + '+' + RULE_VERSION,
        'context': {**result['context'], **siding_context},
        'pending_scope': pending,
        'extra_premises': [
            ('Shortline', 'Carga por eixo', params.axle_load, 't/eixo', f'Seleciona o trilho {rail} e sua montagem na base SIEC.'),
            ('Shortline', 'Desvios de cruzamento', params.sidings, 'un', 'Cada desvio soma seu comprimento útil e dois AMVs.'),
            ('Shortline', 'Comprimento útil por desvio', params.siding_length, 'm', 'Premissa a validar no projeto operacional.'),
            ('Shortline', 'Vias de pátio', params.yard_length, 'm', 'Somadas à via de desvios e pátio.'),
            ('Shortline', 'AMVs de pátio', params.yard_amvs, 'un', 'Somados aos AMVs dos desvios.'),
            ('Shortline', 'Extensão total de via', track_km, 'km', 'Linha principal + desvios + pátio.'),
            ('Escopo pendente', 'Passagens em nível', params.level_crossings, 'un', 'Registrada; não compõe o total.'),
            ('Escopo pendente', 'Locomotivas', params.locomotives, 'un', 'Registrada; não compõe o total.'),
            ('Escopo pendente', 'Vagões', params.wagons, 'un', 'Registrada; não compõe o total.'),
        ]}


def br_list(pending):
    parts = []
    for row in pending:
        quantity = row['quantity']
        parts.append(row['item'].lower() + (f' ({quantity:g} {row["unit"]})' if quantity else ''))
    return ', '.join(parts)


def params_from_scenario(scenario):
    """Reconstrói os parâmetros a partir de um orçamento salvo."""
    defaults = ShortlineParams()
    values = {
        'km': float(scenario.get('km', defaults.km)),
        'sidings': int(scenario.get('sidings', defaults.sidings)),
        'siding_length': float(scenario.get('siding_length', defaults.siding_length)),
        'yard_length': float(scenario.get('yard_length', defaults.yard_length)),
        'yard_amvs': int(scenario.get('yard_amvs', defaults.yard_amvs)),
        'axle_load': float(scenario.get('axle_load', defaults.axle_load)),
        'drainage': scenario.get('drainage', defaults.drainage),
        'fence': scenario.get('fence', defaults.fence) if scenario.get('fence') != 'Nenhuma' else defaults.fence,
        'detection': scenario.get('detection', defaults.detection),
        'level_crossings': int(scenario.get('level_crossings', defaults.level_crossings)),
        'locomotives': int(scenario.get('fleet_locomotives', defaults.locomotives)),
        'wagons': int(scenario.get('fleet_wagons', defaults.wagons)),
    }
    return replace(defaults, **values)


def default_selection(group):
    """Sinalização começa fora do escopo; os demais grupos começam incluídos."""
    return group != '8 Sinalização'

