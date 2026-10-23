"""Conferência independente do elevado de passageiros.

Recalcula as quantidades do elevado diretamente das fórmulas de
``config/rules.json``, com avaliador e leitura de preços próprios (sem usar
``railbudget.expressions`` nem ``railbudget.engine``), e compara item a item
com o motor. Os valores-chave também são conferidos à mão.
"""
from decimal import Decimal, ROUND_HALF_UP
import json
import math
from pathlib import Path
import sqlite3

import pytest

from railbudget.elevated import calculate_elevated
from railbudget.engine import Scenario, load_model


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = dict(configuration="Elevado", km=2.5, lines=2, amvs=2, rolling_stock=False,
    elevated_height=12.0, elevated_span=30.0, elevated_width_double=12.0,
    foundation_type="Hélice contínua", pile_diameter=0.60, foundation_depth=25.0,
    piles_per_support=6, geotechnical_condition="Desfavorável")
GEOTECH = 1.25
FOUNDATION_ROWS = {11, 12, 19, 20, 21, 22, 23, 24, 25, 26}
PILE_CODES = {"mobilization": "SIEC-02.01.04.400.01", "pile": "SIEC-02.01.04.400.07"}


def cents(value):
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def independent_eval(expression, names):
    def roundup(value, digits=0):
        factor = 10 ** digits
        return math.copysign(math.ceil(abs(value) * factor), value) / factor
    scope = {"ceil": math.ceil, "floor": math.floor, "min": min, "max": max, "abs": abs,
        "ROUNDUP": roundup, "PI": lambda: math.pi, **names}
    return float(eval(str(expression).lstrip("=").replace("^", "**"), {"__builtins__": {}}, scope))


def independent_catalog():
    with sqlite3.connect(ROOT / "data" / "catalog.sqlite") as connection:
        connection.row_factory = sqlite3.Row
        catalog = {row["key"]: dict(row) for row in connection.execute("SELECT * FROM prices")}
    for row in json.loads((ROOT / "data" / "scope2_prices.json").read_text(encoding="utf-8")):
        catalog[row["key"]] = row
    return catalog


def independent_quantities(rules):
    s = SCENARIO
    L = s["km"] * 1000
    envelope = rules["profiles"]["siec"]["envelope"]
    c = rules["constants"]
    names = {**rules["parameters"], **c, "km": s["km"], "lines": s["lines"], "amvs": s["amvs"],
        "envelope": envelope, "duration": rules["profiles"]["siec"]["elevated_months"],
        "span": s["elevated_span"], "height": s["elevated_height"],
        "V18": s["piles_per_support"], "V19": s["foundation_depth"]}
    for name, expression in rules["derived"]:
        names[name] = independent_eval(expression, names)
    names["deck_area"] = L * s["elevated_width_double"] + s["amvs"] * envelope * 2

    block = (s["piles_per_support"] / 4) * (s["pile_diameter"] / 0.80) ** 2
    height = s["elevated_height"] / 8
    width = s["elevated_width_double"] / 11
    expected = {}
    for rule in rules["rules"]:
        if rule["profile"] != "siec" or not rule["id"].startswith("vp:Elevado:"):
            continue
        row = int(rule["id"].rsplit(":", 1)[1])
        q = independent_eval(rule["quantity"], names)
        if row == 21:
            q *= (s["pile_diameter"] / 0.80) ** 2
        elif 22 <= row <= 26:
            q *= block
        elif 27 <= row <= 30:
            q *= height
        elif row == 36:
            q *= width
        if row in FOUNDATION_ROWS:
            q *= GEOTECH
        if q:
            expected[rule["id"]] = (q, rule)
    return names, expected


@pytest.fixture(scope="module")
def engine_result():
    rules, catalog = load_model()
    return rules, calculate_elevated(Scenario(**SCENARIO), rules, catalog)


def test_valores_chave_conferidos_a_mao(engine_result):
    rules, result = engine_result
    names, expected = independent_quantities(rules)
    # 2.500 m / 30 m = 83,3 → 84 vãos e 85 apoios.
    assert names["spans"] == 84 and names["supports"] == 85
    assert result["elevated"]["spans"] == 84 and result["elevated"]["supports"] == 85
    # Via dupla: fator de fundação 1,5; condição desfavorável: 1,25.
    assert names["foundation"] == 1.5
    assert expected["vp:Elevado:20"][0] == pytest.approx(85 * 6 * 25 * 1.5 * 1.25)
    # 85 apoios × 20 m de sondagem × 1,25.
    assert expected["vp:Elevado:12"][0] == pytest.approx(85 * 20 * 1.25)
    # Tabuleiro: 2.500 m × 12 m + 2 AMVs × 50 m × 2.
    assert names["deck_area"] == 30200


def test_quantidades_e_totais_do_elevado_reconciliam_com_o_motor(engine_result):
    rules, result = engine_result
    _, expected = independent_quantities(rules)
    catalog = independent_catalog()
    engine_items = {item["id"]: item for item in result["items"] if item["id"].startswith("vp:Elevado:")}
    assert set(engine_items) == set(expected)

    for identifier, (quantity, rule) in expected.items():
        item = engine_items[identifier]
        assert item["quantity"] == pytest.approx(quantity, rel=1e-9), identifier
        row = int(identifier.rsplit(":", 1)[1])
        if row == 19:
            assert item["code"] == PILE_CODES["mobilization"]
        elif row == 20:
            assert item["code"] == PILE_CODES["pile"]
        else:
            priced = [catalog[key] for key in rule["candidates"] if catalog.get(key, {}).get("price") is not None]
            chosen = min(priced, key=lambda price: rules["source_priority"].index(price["source"]))
            assert item["code"] == chosen["code"], identifier
            assert item["unit_cost"] == chosen["price"], identifier
        assert item["total"] == cents(quantity * item["unit_cost"]), identifier


def test_totais_do_orcamento_fecham_com_bdi(engine_result):
    _, result = engine_result
    direct = cents(sum(item["total"] for item in result["items"]))
    assert result["direct"] == direct
    assert result["bdi_amount"] == cents(direct * result["scenario"]["bdi"])
    assert result["total"] == cents(direct + result["bdi_amount"])
    assert result["per_km"] == cents(result["total"] / SCENARIO["km"])
    assert sum(result["groups"].values()) == pytest.approx(result["direct"], abs=0.05)
