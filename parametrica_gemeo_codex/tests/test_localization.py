from railbudget.localization import nome_variavel, formula_legivel


def test_memoria_em_portugues_preserva_expressao_executavel():
    formula = "ceil(L/overhead_span)+amvs*V5"
    assert formula_legivel(formula) == (
        "arredondar para cima(extensão do corredor (m)/"
        "vão dos suportes da rede aérea (m))+quantidade de AMVs*Parâmetro V5"
    )
    assert formula == "ceil(L/overhead_span)+amvs*V5"
    assert nome_variavel("P33") == "Parâmetro P33"
