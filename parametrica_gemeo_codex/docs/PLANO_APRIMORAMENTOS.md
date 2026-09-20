# Aprimoramentos incrementais

## Mapeamento antes das alterações

- `app.py`: formulário por cenário; resultados e arquivos em sessão; comparação A/B; consulta SQLite; conferência dos quatro cenários legados.
- `railbudget/engine.py`: Scenario, validação, seleção de regras, hierarquia de preços, quantitativos e agregação dos seis grupos. Função calculate independente da interface.
- `railbudget/expressions.py`: aritmética restrita e arredondamento monetário.
- `config/rules.json`: regras de composição, geometria e grupos. `coverage.json`: cobertura das EAPs de origem.
- `data/catalog.sqlite`: preços e proveniência; snapshots e inventário preservam as planilhas manuais.
- `railbudget/exporters.py`: Excel com PROCV e fórmulas de quantidade; relatório Word; dois PDFs equivalentes. Ainda não há exportador PowerPoint.
- `tests/`: 24 casos existentes para regressão do cálculo, comparação, consulta e documentos.

## Sequência combinada com o usuário

1. **Concluído:** seleção financeira dos grupos; abas claras de resumo e detalhamento; abas de grupo no Excel; seleção vazia, isolada, múltipla e comparação testadas.
2. **Concluído:** rede aérea, sinalização e material rodante, com composições SIEC, referência contratual CPTM por composição e premissas paramétricas documentadas. A infraestrutura de cabos agora usa banco subterrâneo na superfície e canaletas/passa-fios embutidos no tabuleiro elevado. Os controles redundantes de topografia e banco de dutos foram retirados do formulário lateral.
3. Após confirmação: nomenclatura integralmente em português, incluindo memórias e variáveis exibidas.
4. Após confirmação: figuras e memoriais; incorporar PowerPoint e reutilizar as figuras na interface e documentos.
5. Após confirmação: padronização global Aptos 12, Excel com margens B2, alinhamentos e bordas; cenário de exemplo com verificação visual.

A aplicação está publicada no Streamlit Community Cloud; cada ajuste confirmado pode ser promovido ao repositório principal antes do início da etapa seguinte.
