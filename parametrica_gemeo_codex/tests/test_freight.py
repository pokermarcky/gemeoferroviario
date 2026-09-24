import pytest
from railbudget.engine import Scenario, load_model, calculate, select_groups
from railbudget.freight import calculate_freight


def test_freight_has_distinct_priced_track_and_reacts_to_axle_and_length():
    rules, catalog = load_model()
    passenger = calculate(Scenario(), rules, catalog)
    base = Scenario(rolling_stock=False, trainsets=0, overhead=False,
                    signaling=False, amvs=0, ducts=False)
    light = calculate_freight(base, 20, rules, catalog)
    heavy = calculate_freight(base, 25, rules, catalog)
    long = calculate_freight(Scenario(km=2, rolling_stock=False, trainsets=0,
                                      overhead=False, signaling=False, amvs=0, ducts=False),
                             25, rules, catalog)
    rail = next(i for i in heavy['items'] if i['id'] == 'vp:Superfície:26')
    assembly = next(i for i in heavy['items'] if i['id'] == 'vp:Superfície:33')
    assert rail['code'] == 'SIEC-03.04.01.100.10'
    assert rail['quantity'] == pytest.approx(2 * 1000 * 60 / 1000 * 1.02)
    assert assembly['code'] == 'SIEC-03.03.04.100.03'
    assert heavy['total'] > light['total']
    assert long['total'] > heavy['total']
    assert heavy['total'] < passenger['total']
    assert sum(i['total'] for i in heavy['items']) == heavy['direct']
    assert '9 Material rodante' not in heavy['groups']
    assert select_groups(heavy, list(heavy['groups']))['total'] == heavy['total']
