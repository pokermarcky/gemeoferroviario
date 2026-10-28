# Aprimoramentos incrementais

> **Situação em 28/10/2026.** Etapas 1 a 3 concluídas (a 3 no PR #44). Etapas 4 e 5 continuam pendentes de confirmação; parte da 4 avançou com os downloads de PDF e Word na interface (PR #56). Desde o PR #28 o Excel tem valores fixos, sem PROCV nem fórmulas. Subterrâneo e Shortline já produzem orçamento (ver "Reorganização dos orçamentos"). O histórico detalhado está em `docs/CHANGELOG.md`.

## Mapeamento antes das alterações

- `app.py`: formulário por cenário; resultados e arquivos em sessão; comparação A/B; consulta SQLite; conferência dos quatro cenários legados.
- `railbudget/engine.py`: Scenario, validação, seleção de regras, hierarquia de preços, quantitativos e agregação dos seis grupos. Função calculate independente da interface.
- `railbudget/expressions.py`: aritmética restrita e arredondamento monetário.
- `config/rules.json`: regras de composição, geometria e grupos. `coverage.json`: cobertura das EAPs de origem.
- `data/catalog.sqlite`: preços e proveniência; snapshots e inventário preservam as planilhas manuais.
- `railbudget/exporters.py`: Excel com PROCV e fórmulas de quantidade; relatório Word; dois PDFs equivalentes. Ainda não há exportador PowerPoint. *(Atualização: desde o PR #28 o Excel tem valores fixos; Word e PDF voltaram à interface no PR #56.)*
- `tests/`: 24 casos existentes para regressão do cálculo, comparação, consulta e documentos.

## Sequência combinada com o usuário

1. **Concluído:** seleção financeira dos grupos; abas claras de resumo e detalhamento; abas de grupo no Excel; seleção vazia, isolada, múltipla e comparação testadas.
2. **Concluído:** rede aérea, sinalização e material rodante, com composições SIEC, referência contratual CPTM por composição e premissas paramétricas documentadas. A infraestrutura de cabos agora usa banco subterrâneo na superfície e canaletas/passa-fios embutidos no tabuleiro elevado. Os controles redundantes de topografia e banco de dutos foram retirados do formulário lateral.
3. **Concluído (PR #44):** nomenclatura integralmente em português nas memórias de cálculo. ROUNDUP/ROUNDDOWN e PI() aparecem como "arredondar para cima/baixo" e π; decimais usam vírgula, argumentos usam ponto e vírgula e operadores usam × e ÷; a origem das regras (vp, p2, subterraneo) é exibida por extenso também no Word e no PDF. As expressões executáveis, chaves de rules.json e dados salvos não mudam.
4. Após confirmação (pendente; downloads de PDF e Word já disponíveis): figuras e memoriais; incorporar PowerPoint e reutilizar as figuras na interface e documentos.
5. Após confirmação: padronização global Aptos 12, Excel com margens B2, alinhamentos e bordas; cenário de exemplo com verificação visual.

A aplicação está publicada no Streamlit Community Cloud; cada ajuste confirmado pode ser promovido ao repositório principal antes do início da etapa seguinte.

## Reorganização dos orçamentos

- A interface passa a ter **ORÇAMENTOS** com quatro abas: Ferrovia de passageiro, Ferrovia de carga, VLT - Veículo leve sobre Trilho e Shortline.
- Passageiros conserva apenas SIEC • lastro / AMV nº 14 na interface, superfície/elevado e o Excel do orçamento. O banco de dutos volta a aparecer explicitamente entre os grupos de superfície. O prazo deixa de ser informado pelo usuário; o motor adota a referência do modelo.
- Subterrâneo produz uma estimativa preliminar por equivalência SIEC (`underground.py`), com aviso na tela; não reaproveita totais de superfície como subterrâneos. *(A versão inicial bloqueava o cálculo.)*
- Carga, VLT e Shortline têm orçamento próprio: carga e Shortline com composições SIEC de carga (carga por eixo, PRs #52 e #53) e VLT pelo edital Aeroporto - Castelão. Nenhum valor de passageiro é reutilizado como custo dessas modalidades.
