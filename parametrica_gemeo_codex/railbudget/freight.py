"""Adaptação explícita da via de carga aos itens precificados na base SIEC.

A carga por eixo seleciona uma faixa de `config/freight_axle.json`. A faixa
define o perfil de trilho e os padrões editáveis de espaçamento de dormentes,
altura de lastro e espessura de sublastro; a plataforma acompanha a base do
lastro. Preços e códigos continuam vindo da SIEC; as premissas geométricas são
preliminares e ficam visíveis no resultado e no Excel.
"""

import json
import math
from collections import Counter
from pathlib import Path
from .engine import calculate, money

ROOT = Path(__file__).resolve().parents[1]
PREMISE_KEYS = ('sleeper_spacing', 'ballast_depth', 'sublayer_thickness')
PENDING_FIELDS = (
    ('locomotives', 'Locomotivas equivalentes', 'un/km',
     'A SIEC tem custo horário de operação, não preço de aquisição.'),
    ('wagons', 'Vagões equivalentes', 'un/km',
     'A SIEC tem custo horário de operação, não preço de aquisição.'),
    ('yards', 'Pátios de cruzamento ou terminais', 'un',
     'Arranjo de linhas, AMVs e edificações depende de projeto operacional.'),
    ('bridge_length', 'Pontes e viadutos (obras de arte especiais)', 'm',
     'Depende de vão, fundação e trem-tipo de carga; a referência do elevado é de passageiros.'),
    ('level_crossings', 'Passagens em nível', 'un',
     'Tipo de proteção e pavimento dependem da via cruzada.'),
)


def load_axle_config(root=ROOT):
    return json.loads((Path(root) / 'config/freight_axle.json').read_text(encoding='utf-8'))


def axle_class(axle_load, config=None):
    """Faixa da carga por eixo; acima do limite não há trilho precificado."""
    config = config or load_axle_config()
    axle_load = float(axle_load)
    if not config['min_axle_load'] <= axle_load <= config['max_axle_load']:
        raise ValueError(f"Carga por eixo deve estar entre {config['min_axle_load']:g} e "
                         f"{config['max_axle_load']:g} t/eixo. " + config['above_max_note'])
    return next(c for c in config['classes'] if axle_load <= c['max_axle_load'])


def default_premises(axle_load, config=None):
    return dict(axle_class(axle_load, config)['defaults'])


def platform_width(ballast_depth, config=None):
    """Largura da plataforma = base do lastro + banquetas da referência."""
    g = (config or load_axle_config())['reference_geometry']
    height = ballast_depth + g['sleeper_height']
    return g['ballast_top_width'] + 2 * g['ballast_slope'] * height + 2 * g['platform_margin']


def freight_input_signature(axle_load, premises, pending):
    """Assinatura comparável das entradas próprias de carga, usada para indicar recálculo."""
    return (float(axle_load), tuple(float(premises.get(k, 0)) for k in PREMISE_KEYS),
            tuple(float(pending.get(k, 0)) for k, *_ in PENDING_FIELDS))


def pending_scope(pending):
    """Itens de carga registrados fora do total, com motivo; nunca recebem preço."""
    return [{'key': key, 'item': label, 'quantity': float(pending.get(key, 0) or 0), 'unit': unit,
             'status': 'Não precificado · fora do total', 'reason': reason}
            for key, label, unit, reason in PENDING_FIELDS]


def _price(catalog, code, unit):
    row = next((r for r in catalog.values() if r['code'] == code and r['source'] == 'SIEC'
                and r['price'] is not None), None)
    if row is None or row['unit'] != unit:
        raise ValueError('Preço SIEC de carga indisponível ou com unidade incompatível: ' + code)
    return row


def _set(item, quantity, formula, note, catalog=None, code=None):
    if code and code != item['code']:
        price = _price(catalog, code, item['unit'])
        item.update(code=code, source=price['source'], description=price['description'],
                    unit_cost=price['price'], price_key=price['key'], date=price['date'],
                    provenance=price['provenance'])
    item.update(quantity=quantity, quantity_formula=formula, note=note)
    item['total'] = money(quantity * item['unit_cost'])


def calculate_freight(scenario, axle_load, rules, catalog, premises=None, pending=None, config=None):
    """Orça infraestrutura de carga, redimensionando a via pela carga por eixo.

    Trilho, dormentes, fixações, lastro, sublastro e plataforma acompanham a
    faixa de carga e as premissas informadas. Frota, pátios, obras de arte e
    passagens em nível são listados em `pending_scope`, fora do total.
    """
    config = config or load_axle_config()
    if scenario.configuration != 'Superfície' or scenario.rolling_stock:
        raise ValueError('O modelo preliminar de carga cobre apenas a infraestrutura em superfície.')
    klass = axle_class(axle_load, config)
    values = {**klass['defaults'], **{k: float(v) for k, v in (premises or {}).items() if k in PREMISE_KEYS}}
    for key, (low, high) in config['limits'].items():
        if not low <= values[key] <= high:
            raise ValueError(f'Premissa de carga fora da faixa preliminar ({key}): use entre {low:g} e {high:g} m.')
    g = config['reference_geometry']
    result = calculate(scenario, rules, catalog)
    ctx = result['context']
    lines, L, amvs, envelope = ctx['lines'], ctx['L'], ctx['amvs'], ctx['envelope']
    low_amvs, extra, run = ctx['low_amvs'], ctx['extra'], ctx['run']
    spacing, depth, sublayer = values['sleeper_spacing'], values['ballast_depth'], values['sublayer_thickness']
    sleepers = ((lines - extra) * math.ceil((L - low_amvs * envelope) / spacing - 1e-9)
                + extra * math.ceil((L - (low_amvs + 1) * envelope) / spacing - 1e-9))
    height = depth + g['sleeper_height']
    section = height * (g['ballast_top_width'] + g['ballast_slope'] * height)
    ballast = (section * run - sleepers * 2.8 * 0.28 * 0.2 + 3.5 * amvs * envelope
               - 300 * amvs * 0.28 * 0.2) * 1.1
    width = platform_width(depth, config)
    double_add = ctx['double_width_add'] * (lines - 1)
    width_factor = (width + double_add) / (g['platform_width'] + double_add)
    surface = L * (width + double_add) + amvs * envelope * 2
    ctx.update(axle_load=float(axle_load), rail_kg_m=klass['rail_kg_m'], sleeper_spacing=spacing,
               ballast_depth=depth, sublayer_thickness=sublayer, freight_platform_width=width,
               freight_platform_factor=width_factor, freight_sleepers=sleepers,
               freight_ballast_section=section, freight_ballast=ballast, freight_surface_area=surface)
    codes = klass['codes']
    premise = 'Premissa de carga a validar em projeto (ISF-212/213 DNIT).'
    for item in result['items']:
        if not item['id'].startswith('vp:Superfície:'):
            continue
        row = int(item['id'].rsplit(':', 1)[1])
        if 19 <= row <= 23:
            _set(item, item['quantity'] * width_factor, item['quantity_formula'] + '*freight_platform_factor',
                 f'{item["note"]}. Plataforma de carga de {width:.2f} m. {premise}')
        elif row == 24:
            _set(item, surface, 'freight_surface_area', f'Plataforma de carga de {width:.2f} m. {premise}')
        elif row == 25:
            _set(item, surface * sublayer, 'freight_surface_area*sublayer_thickness',
                 f'Sublastro de {sublayer * 100:.0f} cm sobre a plataforma de carga. {premise}')
        elif row == 26:
            _set(item, 2 * run * klass['rail_kg_m'] / 1000 * 1.02, '2*run*rail_kg_m/1000*1.02',
                 f'Trilho {klass["rail"]}; duas filas; 2% perda. {premise}', catalog, codes['rail'])
        elif row == 27:
            _set(item, sleepers, 'freight_sleepers',
                 f'Dormente de concreto para {klass["rail"]}, espaçamento {spacing:.2f} m. {premise}',
                 catalog, codes['sleeper'])
        elif row in (28, 29, 30):
            per = 2 if row == 30 else 4
            _set(item, sleepers * per, f'freight_sleepers*{per}',
                 f'{per} un por dormente; espaçamento {spacing:.2f} m. {premise}')
        elif row == 31:
            _set(item, ballast, 'freight_ballast',
                 f'Lastro de {depth * 100:.0f} cm sob o dormente; talude 1,5:1; 10% perdas. {premise}')
        elif row == 32:
            _set(item, ballast * ctx['V23'], 'freight_ballast*V23', item['note'])
        elif row == 33:
            _set(item, item['quantity'], item['quantity_formula'],
                 f'Montagem para trilho {klass["rail"]}. {premise}', catalog, codes['assembly'])
        elif row == 36:
            _set(item, item['quantity'], item['quantity_formula'],
                 f'Solda aluminotérmica para {klass["rail"]}. {premise}', catalog, codes['weld'])
    pending = dict(pending or {})
    result['scenario'].update(axle_load=float(axle_load), axle_class=klass['id'],
                              freight_premises={**values, 'platform_width': width},
                              **{k: float(pending.get(k, 0) or 0) for k, *_ in PENDING_FIELDS})
    result['freight'] = {'class': klass['id'], 'class_label': klass['label'], 'rail': klass['rail'],
                         'rail_kg_m': klass['rail_kg_m'], 'premises': values, 'platform_width': width,
                         'sleepers': sleepers, 'ballast': ballast, 'defaults': klass['defaults'],
                         'status': config['status']}
    result['pending_scope'] = pending_scope(pending)
    result['model_label'] = f'SIEC • carga / {klass["rail"].replace(" ", "").replace("-", "")} · premissa {float(axle_load):g} t/eixo'
    result['groups'] = {grp: money(sum(i['total'] for i in result['items'] if i['group'] == grp))
                        for grp in rules['groups'] if not grp.startswith('9 ')}
    result['direct'] = money(sum(result['groups'].values()))
    result['bdi_amount'] = money(result['direct'] * scenario.bdi)
    result['total'] = money(result['direct'] + result['bdi_amount'])
    result['per_km'] = money(result['total'] / scenario.km)
    result['per_line_km'] = money(result['total'] / (scenario.km * scenario.lines))
    result['counts'] = dict(Counter(i['source'] for i in result['items']))
    result['warnings'].append(
        f'Carga por eixo de {float(axle_load):g} t: faixa {klass["label"]}. Trilho, dormentes, fixações, '
        f'lastro ({depth * 100:.0f} cm), sublastro ({sublayer * 100:.0f} cm) e plataforma ({width:.2f} m) '
        'foram redimensionados por premissas preliminares a validar em projeto (ISF-212/213 DNIT). '
        'AMVs, drenagem e vedação seguem a referência SIEC.')
    listed = [f'{p["item"].lower()} ({p["quantity"]:g} {p["unit"]})' for p in result['pending_scope'] if p['quantity']]
    result['warnings'].append('Fora do total, sem preço na base: frota, pátios, terminais, obras de arte especiais e '
                              'passagens em nível.' + (' Informado: ' + '; '.join(listed) + '.' if listed else ''))
    return result
