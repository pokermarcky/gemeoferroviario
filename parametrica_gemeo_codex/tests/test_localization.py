from railbudget.localization import nome_variavel, formula_legivel, memoria_quantidade, origem_legivel


def test_memoria_em_portugues_preserva_expressao_executavel():
    formula = "ceil(L/overhead_span)+amvs*V5"
    assert formula_legivel(formula) == (
        "arredondar para cima(extensão do corredor (m) ÷ "
        "vão dos suportes da rede aérea (m))+quantidade de AMVs × extensão do corredor"
    )
    assert formula == "ceil(L/overhead_span)+amvs*V5"
    assert nome_variavel("P33") == "horas previstas de bombeamento"


def test_memoria_traduz_funcoes_do_excel_e_usa_notacao_brasileira():
    formula = "(P5-(ROUNDUP(P5/P29,0)+1)*1.6)*(0.6*0.45-P30*PI()*0.11^2/4)"
    texto = formula_legivel(formula)
    assert texto == (
        "(extensão do corredor-(arredondar para cima(extensão do corredor ÷ espaçamento entre caixas)+1) × 1,6)"
        " × (0,6 × 0,45-quantidade de dutos × π × 0,11^2 ÷ 4)"
    )
    assert "ROUNDUP" not in texto and "PI" not in texto
    assert formula_legivel("min(lines,2)*0.5") == "mínimo(quantidade de vias; 2) × 0,5"


def test_memoria_avaliada_nao_mistura_ponto_decimal_com_milhar():
    texto = memoria_quantidade("ROUNDUP(P5/50,0)+1", {"P5": 1000}, 21, "un")
    assert texto == "arredondar para cima(extensão do corredor (1.000 m) ÷ 50)+1 = 21 un"


def test_origem_da_regra_aparece_por_extenso():
    assert origem_legivel("p2") == "Referência histórica"
    assert origem_legivel("vp") == "Via permanente"
    assert origem_legivel("subterraneo") == "Modelo subterrâneo preliminar"
    assert origem_legivel("Premissa do usuário") == "Premissa do usuário"
