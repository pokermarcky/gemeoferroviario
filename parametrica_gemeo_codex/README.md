# Gêmeo Ferroviário Paramétrico

Aplicação Streamlit para orçamentos paramétricos ferroviários. O cálculo disponível usa a base **SIEC • lastro / AMV nº 14** para ferrovia de passageiros em superfície ou elevado, com EAP, BDI editável, custos por km e orçamento em Excel.

## Uso

```powershell
streamlit run app.py
```

Abra **ORÇAMENTOS → Ferrovia de passageiro**, informe a extensão, configuração e quantidade de vias, escolha os grupos de serviço e clique em **Calcular orçamento**. O botão **Baixar orçamento em Excel** entrega a planilha do cenário calculado e dos grupos atualmente selecionados. As abas **Resumo geral** e **Detalhamento por grupo** mostram o resultado na página.

**Banco de dutos** aparece entre os grupos de superfície e corresponde ao banco subterrâneo de seis dutos. Em elevado, o mesmo grupo passa a **Canaletas e passa-fios**, conforme as composições aplicáveis. O controle de prazo foi retirado do formulário; o cálculo conserva o prazo de referência interno do modelo para os quantitativos que dependem dele.

A opção **Subterrâneo** está visível, mas não produz orçamento até serem cadastrados quantitativos e preços próprios de túneis e sistemas associados. As abas **Ferrovia de carga**, **VLT - Veículo leve sobre Trilho** e **Shortline** apresentam o escopo de dados necessário para construir seus modelos; não atribuem custos de passageiros a essas modalidades.

O resultado indica o último cenário submetido. Alterações no formulário só entram no orçamento depois de clicar em **Calcular orçamento**; marcar e desmarcar grupos e alterar o BDI fazem um recorte financeiro imediato do resultado existente. Os resultados de sessão não persistem ao encerrar o servidor.

## Bases e premissas

- O banco `data/catalog.sqlite` contém 13.260 referências originais; `data/scope2_prices.json` acrescenta uma referência contratual da frota, totalizando 13.261 registros carregados.
- A via e o AMV nº 14 usam composições SIEC. A referência de material rodante vem do contrato CPTM 8186142011, data-base abril/2016, sem reajuste monetário. A extrapolação para via dupla SIEC é identificada nas regras.
- O número de AMVs informado é **total no corredor**, distribuído entre as linhas. Seu envelope é abatido da via corrida.
- A seleção de grupos não redimensiona geometria, duração, plataforma ou envelopes de AMV. Quantidades e valores são estimativas paramétricas, sujeitas a projeto e validação dos preços.
- As tabelas históricas do legado Parte 2 continuam no projeto para rastreabilidade e regressão interna, mas esse modelo não é oferecido na interface.
- Não havia bases SINAPI/SICRO nas planilhas recebidas. A hierarquia de fontes está no motor, sem inventar preços ou equivalências.

## Estrutura

```text
app.py                         interface Streamlit e navegação
railbudget/engine.py           cenários, seleção, quantitativos e preços
railbudget/exporters.py        planilha Excel e exportadores internos
railbudget/localization.py     rótulos e memórias em português
config/rules.json              composições e parâmetros
config/coverage.json           cobertura da EAP de origem
data/catalog.sqlite           catálogo de preços
data/scope2_prices.json       referência contratual de material rodante
docs/MAPEAMENTO.md             decisões técnicas
tests/                         regressões de cálculo, interface e exportação
```

## Validação

Execute `python -m pytest -q` com as dependências de `requirements-dev.txt`. As regressões mantêm a reprodução dos quatro totais históricos da Parte 2 para auditoria, além dos cenários SIEC e da geração de documentos. A interface publica somente o orçamento Excel do modelo SIEC para passageiros.

A aplicação pode ser executada localmente ou no Streamlit Community Cloud. As fórmulas e referências do Excel são calculáveis e os identificadores internos do motor não são alterados pelos rótulos de apresentação.
