"""Base SIEC enviada com códigos sem o prefixo "SIEC-" (caso real da data-base agosto/2026)."""
import pytest

from railbudget.elevated import calculate_elevated
from railbudget.engine import Scenario, calculate, load_model
from railbudget.reference_data import ReferenceBase, apply_reference_bases, stale_price_warning


@pytest.fixture(scope="module")
def model():
    return load_model()


def _upload(catalog, rewrite, factor=1.10, skip=()):
    records = [
        {"code": rewrite(row["code"]), "description": row["description"], "unit": row["unit"],
         "price": row["price"] * factor, "date": "08/2026"}
        for row in catalog.values()
        if row["source"] == "SIEC" and row["kind"] == "Serviços" and row["price"] is not None
        and row["code"] not in skip
    ]
    base = ReferenceBase("SIEC", "Serviços", "08/2026", "siec_ago2026.xlsx", "teste", records, [], [])
    return {("SIEC", "Serviços"): base}


@pytest.mark.parametrize("rewrite", [
    lambda code: code.replace("SIEC-", ""),
    lambda code: code.replace("SIEC-", "SIEC "),
    lambda code: code,
])
@pytest.mark.parametrize("foundation", ["Hélice contínua", "Estaca raiz"])
def test_elevado_calcula_com_base_enviada(model, rewrite, foundation):
    rules, catalog = model
    bases = _upload(catalog, rewrite)
    updated, _ = apply_reference_bases(catalog, bases)
    diameter = 0.80 if foundation == "Hélice contínua" else 0.41
    scenario = Scenario(configuration="Elevado", foundation_type=foundation, pile_diameter=diameter)
    result = calculate(scenario, rules, updated)
    piles = [item for item in result["items"] if item["id"] in ("vp:Elevado:19", "vp:Elevado:20")]
    assert len(piles) == 2
    for item in piles:
        assert item["date"] == "08/2026"
        assert item["provenance"].startswith("Upload ativo")
    assert calculate_elevated(scenario, rules, updated)["total"] > 0
    assert stale_price_warning(result["items"], bases) is None


def test_preco_da_fundacao_vem_da_base_enviada(model):
    rules, catalog = model
    original = calculate(Scenario(configuration="Elevado"), rules, catalog)
    updated, _ = apply_reference_bases(catalog, _upload(catalog, lambda c: c.replace("SIEC-", ""), 1.10))
    result = calculate(Scenario(configuration="Elevado"), rules, updated)
    before = {item["id"]: item["unit_cost"] for item in original["items"]}
    for item in result["items"]:
        if item["id"] in ("vp:Elevado:19", "vp:Elevado:20"):
            assert item["unit_cost"] == pytest.approx(before[item["id"]] * 1.10)


def test_aviso_de_codigo_ausente_na_base_enviada(model):
    rules, catalog = model
    bases = _upload(catalog, lambda c: c, skip={"SIEC-02.01.04.400.01"})
    updated, _ = apply_reference_bases(catalog, bases)
    result = calculate(Scenario(configuration="Elevado"), rules, updated)
    notice = stale_price_warning(result["items"], bases)
    assert notice and "SIEC-02.01.04.400.01" in notice and "junho/2026" in notice
