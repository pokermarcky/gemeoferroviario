# Histórico de alterações

Ponto de restauração anterior a estas alterações: branch `backup/estavel-2026-10-23` (commit `08fdea8`).

## 2026-10-23 — Aba Shortline (PR #53)

- Aba **Shortline** preenchida: ferrovia de carga curta em via singela, superfície, tração diesel. Linha principal pelo motor de carga (`calculate_freight`, carga por eixo de 16 a 25 t com TR-57 ou UIC 60), desvios de cruzamento e vias de pátio com as mesmas composições SIEC da via corrida (sem repetir canteiro, sondagens e administração local), 2 AMVs por desvio + AMVs de pátio, BDI editável, Excel e reabertura de projetos salvos.
- Passagens em nível, locomotivas, vagões, terminais e obras de arte especiais ficam registrados como escopo pendente, fora do total. Nenhum preço novo.
- Novo módulo `railbudget/shortline.py`; ajustes aditivos em `app.py`, `user_workspace.py`, `exporters.py` (premissas extras) e `localization.py` (prefixo "desvios e pátio"). Sem mudança em `engine.py`, `freight.py`, `data/` ou `config/`; Passageiro, Carga e VLT inalterados.
- Testes: 100 antes, 108 depois (`tests/test_shortline.py` e `tests/test_app.py`).

## 2026-10-23 — Auditoria de segurança, persistência, elevado e Excel

- Relatório completo em `docs/AUDITORIA.md`. Nenhum secret real no repositório nem no histórico.
- Testes novos: persistência da carteira com Supabase simulado e SQLite (`tests/test_persistencia.py`), conferência independente do elevado (`tests/test_elevado_independente.py`) e integridade do Excel (`tests/test_excel_integridade.py`).
- Excel: textos da EAP e das abas de grupo deixam de citar PROCV/vínculos, pois o arquivo traz valores fixos desde o PR #28.
- Removidos do Git os `.pyc` de `railbudget/__pycache__/`.
- Sem mudança de cálculo, preços ou dados. Testes: 85 antes, 100 depois.

## 2026-10-23 — Carga por eixo redimensiona a via de carga

- `config/freight_axle.json` (novo) e `railbudget/freight.py`: carga por eixo de 16 a 25 t em duas faixas (TR-57 até 20 t; UIC 60 acima). Trilho, dormentes, fixações, lastro, transporte de brita, sublastro e plataforma passam a ser redimensionados; dormente e solda usam o código SIEC do perfil UIC 60. Acima de 25 t o cálculo é recusado (sem preço SIEC do trilho TR-68).
- Formulário de carga: carga por eixo numérica, painel "Premissas técnicas da via de carga (a validar)" e campos de pátios, pontes/viadutos e passagens em nível. Esses itens e a frota ficam em lista separada, fora do total, no resultado e no Excel.
- Impacto: 20 t/eixo mantém exatamente o valor anterior. 25 t/eixo sobe cerca de 1,2% a 1,4% (lastro de 35 cm, plataforma de 6,15 m e solda UIC 60). Passageiros, VLT, identificadores do motor e orçamentos salvos não mudam; orçamentos de carga antigos reabrem com a geometria original.
- Documentação em `docs/MAPEAMENTO.md` (seção "Ferrovia de carga: carga por eixo") e `README.md`. Testes: 78 antes, 85 depois.

## 2026-10-23 — Memórias de cálculo em português (PR #44)

- `railbudget/localization.py`: `ROUNDUP`/`ROUNDDOWN` aparecem como "arredondar para cima/baixo" sem o argumento de casas; `PI()` aparece como π; decimais com vírgula, argumentos separados por ponto e vírgula e operadores × e ÷.
- Origem das regras (`vp`, `p2`, `Ajuste 2`, `subterraneo`) exibida por extenso no Excel, Word e PDF (`origem_legivel`).
- Somente apresentação: expressões executáveis, chaves de `config/rules.json`, fórmulas do Excel e orçamentos salvos não mudam.
- Testes: 75 antes, 78 depois (`tests/test_localization.py`).
