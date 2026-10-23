# Histórico de alterações

Ponto de restauração anterior a estas alterações: branch `backup/estavel-2026-10-23` (commit `08fdea8`).

## 2026-10-23 — Memórias de cálculo em português (PR #44)

- `railbudget/localization.py`: `ROUNDUP`/`ROUNDDOWN` aparecem como "arredondar para cima/baixo" sem o argumento de casas; `PI()` aparece como π; decimais com vírgula, argumentos separados por ponto e vírgula e operadores × e ÷.
- Origem das regras (`vp`, `p2`, `Ajuste 2`, `subterraneo`) exibida por extenso no Excel, Word e PDF (`origem_legivel`).
- Somente apresentação: expressões executáveis, chaves de `config/rules.json`, fórmulas do Excel e orçamentos salvos não mudam.
- Testes: 75 antes, 78 depois (`tests/test_localization.py`).
