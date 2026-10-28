# Histórico de alterações

Ponto de restauração anterior a estas alterações: branch `backup/estavel-2026-10-23` (commit `08fdea8`).

## 2026-10-28 — Downloads em PDF e Word; limite da demonstração no VLT (melhoria 2)

- Passageiro, Carga e Shortline passam a oferecer, além do Excel, **PDF resumido**, **PDF detalhado** e **relatório Word**. Os geradores (`make_pdf`, `make_word` em `exporters.py`) já existiam e eram testados, mas não tinham botão. Os arquivos refletem o recorte exibido (grupos marcados e BDI).
- O botão do Excel passa a se chamar "Excel" dentro do bloco "Baixar orçamento"; a chave interna `<aba>_excel` não muda.
- Demonstração: continua com um único download por sessão, agora em qualquer formato. O Excel do VLT não consumia esse limite e foi corrigido; o arquivo do VLT também passou a ser guardado em cache em vez de regenerado a cada interação.
- Sem mudança de cálculo, preços ou dados. Testes: 110 antes, 111 depois.

## 2026-10-28 — Indicadores por km corretos (melhoria 1)

Ponto de restauração destas melhorias: branch `backup/pre-melhorias-2026-10-28` (main após o PR #54/#53).

- Shortline: o custo por km de via passa a acompanhar os grupos marcados e o BDI. Antes vinha do orçamento completo (com sinalização e BDI, mesmo desmarcados): no cenário padrão a tela mostrava R$ 7.099.006,38; o valor correto é R$ 7.000.316,78 com BDI. O terceiro cartão da Shortline agora é "Por km de via" (principal + desvios + pátio) em vez de "Por km de linha", que repetia o valor por km de corredor.
- Passageiro: quando há material rodante, dois cartões novos mostram a frota incluída no total e a **infraestrutura por km** sem a frota. Os cartões existentes não mudam.
- Excel (aba Resumo): linhas novas "R$/km de via" (Shortline) e "Frota" / "R$/km corredor sem frota" (quando há frota).
- `select_groups` (engine.py) ganha chaves aditivas `fleet_total`, `per_km_without_fleet` e `per_track_km`; nenhum total, regra, preço ou dado salvo muda.
- Testes: 108 antes, 110 depois.

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
