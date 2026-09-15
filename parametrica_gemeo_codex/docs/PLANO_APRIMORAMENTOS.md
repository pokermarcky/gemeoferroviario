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

1. Seleção financeira dos grupos e visualização segregada; abas de grupo no Excel. Preservar as quantidades do cenário de referência e explicitar a base das participações. Testar seleção vazia, isolada, múltipla, comparação e descarte de downloads antigos.
2. Após confirmação: rede aérea, sinalização e material rodante; validar referências e registrar lacunas de preços sem inventar valores.
3. Após confirmação: nomenclatura integralmente em português, incluindo memórias e variáveis exibidas.
4. Após confirmação: figuras e memoriais; incorporar PowerPoint e reutilizar as figuras na interface e documentos.
5. Após confirmação: padronização global Aptos 12, Excel com margens B2, alinhamentos e bordas; cenário de exemplo com verificação visual.

A publicação no Streamlit Community Cloud permanece preparada, mas depende da autenticação do usuário. Esta sequência de aprimoramentos deve ser concluída antes de publicar a versão atualizada.
