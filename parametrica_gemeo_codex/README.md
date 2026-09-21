# Parametric Rails

Aplicação **Streamlit** que consolida bases técnicas ferroviárias. Calcula EAP, custo total com BDI e custos por km de corredor e de linha. Inclui comparação lado a lado, pesquisa das bases e downloads Excel, Word e dois PDFs.

## Uso

No ambiente Python do projeto, a única forma de uso da aplicação é:

```powershell
streamlit run app.py
```

Abra o endereço local mostrado pelo Streamlit. Preencha o formulário e clique em **Calcular Orçamento**. Para baixar documentos, clique em **Preparar arquivos para download** e escolha Excel, Word, PDF do orçamento ou PDF do relatório. As abas **Comparar cenários**, **Base de dados** e **Regras e validação** concentram as demais funções. Não há versão CLI ou notebook para o usuário.

O resultado mostrado pertence ao último formulário enviado, identificado no cabeçalho. Alterações ainda não enviadas não modificam o orçamento. Downloads sempre usam o cenário calculado, não o formulário pendente. Ao calcular novamente, os downloads anteriores são descartados. Resultados de sessão não persistem ao encerrar o servidor.

### Preparação do ambiente

Python 3.12 recomendado. O ambiente `.venv` já foi preparado nesta máquina. Para ativá-lo no PowerShell, execute `.\.venv\Scripts\Activate.ps1` dentro da pasta do projeto. Em outra instalação, crie um ambiente Python e instale as dependências de `requirements.txt` com pip. Essa preparação não é um modo alternativo de uso da aplicação.

A aplicação pode ser executada localmente ou no Streamlit Community Cloud. Não depende das pastas originais após a extração; o banco local, as regras e a documentação acompanham o projeto. PDFs usam ReportLab, sem necessidade de Office ou LibreOffice. São versões equivalentes do mesmo resultado, com paginação própria, e não impressões idênticas do Excel/Word.

## Modelos

### Resumo geral e detalhamento por grupo — Ajuste 1

Não há barra lateral. As características gerais ficam em um bloco compacto e os nove grupos aparecem logo abaixo de **Selecionar todas** e **Desmarcar todas**. Marcar um grupo abre suas opções específicas: tipo de drenagem, Cerca ou Muro, quantidade de AMVs, tecnologia de detecção e quantidade de composições. Desmarcar um grupo recolhe essas opções e remove seu custo do total. Cada cenário A/B conserva sua configuração de forma independente.

O orçamento usa duas abas claras: **Resumo geral**, com participação por grupo, gráfico e EAP consolidada; e **Detalhamento por grupo**, com subtotal direto, subtotal com BDI, custo por km, participação e composição recolhida por padrão. Os grupos excluídos continuam mostrando seu custo de referência, claramente identificado, com participação zero. Os indicadores principais mostram o total selecionado com BDI, aplicado uma única vez.

Em superfície, **Infraestrutura de cabos** representa o banco subterrâneo de seis dutos; no elevado, representa canaletas e passa-fios embutidos no tabuleiro, sem banco enterrado.

Para consultar muro por km, selecione **Muro** no formulário, calcule e mantenha apenas **Vedação** marcada. Para drenagem ou dutos, mantenha apenas o grupo correspondente. Grupos sem serviços seguem com custo zero conforme os parâmetros do formulário.

A seleção é financeira: não redimensiona geometria, duração, plataforma nem abatimentos de AMVs da via corrida. As notas dos documentos identificam os grupos efetivamente incluídos. Alterar a seleção descarta os arquivos preparados anteriormente.

O Excel inclui uma aba por grupo, além de **Resumo** e **EAP** consolidados. As células das novas abas se vinculam à EAP, de modo que alterações de preços se propagam. Grupos excluídos têm uma aba identificada sem serviços incluídos. As novas abas começam em B2, com fonte Aptos 12, alinhamento e bordas; a padronização global das abas e documentos existentes está reservada ao Ajuste 5.

### Rede aérea, sinalização e material rodante — Ajuste 2

A rede aérea inclui postes e sua implantação, mísulas, cabo mensageiro, fio de contato, isoladores, aparelhos de tensionamento e seccionamentos elétricos e mecânicos. As quantidades usam vãos paramétricos de 50 m, trechos de tensionamento de 1,5 km e seccionamentos a cada 3 km ou fração. Os preços são SIEC de junho/2026.

A sinalização inclui sinais, detecção de trens, acionamento dos AMVs, intertravamento, cabo óptico e testes integrados. O usuário escolhe **Circuito de via** ou **Contador de eixos**; as alternativas não são somadas. A estimativa adota blocos de 500 m e um setor de intertravamento a cada 10 km ou fração.

O material rodante é calculado pela quantidade de composições de oito carros informada pelo usuário. A referência unitária é R$ 39.590.100,875 por composição, obtida do contrato CPTM 8186142011 (R$ 316.720.807,00 para oito trens; data-base abril/2016), sem reajuste monetário. O subtotal representa o custo da frota; o indicador por km apenas rateia esse custo pela extensão atendida.

- **SIEC (padrão):** via lastreada e AMV nº14 do VPCODEX2026; complementos gerais da Parte 2. Remove topografia, drenagem e dutos anteriores antes de inserir os substitutos. Preserva proteções do tabuleiro como grupo 1; vedação da faixa é outra função.
- **Legado Parte 2:** reproduz os quatro orçamentos anteriores, incluindo elevado em placa e AMV nº9 com preços provisórios. Não atribui o preço nº14 ao nº9.
- **Via dupla SIEC:** extrapolação explícita de plataforma compartilhada e fatores de gestão/fundações em `config/rules.json`; não existe planilha manual prévia dessa combinação. Não equivale a dimensionamento estrutural.
- AMVs são quantidade **total**, não por linha nem por km. Envelopes são abatidos da via corrida e distribuídos entre linhas. Prazo 0 utiliza a referência do modelo; é possível informar prazo específico.

## Rastreabilidade e dados

O catálogo carregado tem 13.261 referências: 13.260 do banco original e uma referência contratual adicional de material rodante em `data/scope2_prices.json`. São 13.176 registros SIEC, 83 registros herdados e 2 referências de mercado/contrato. Os 83 registros incluem rateios informativos não somados ao orçamento. Linhas sem preço permanecem `NULL`, nunca zero. Fontes duplicadas foram unificadas, preservando a rastreabilidade técnica por fonte, aba e linha.

Caminhos locais, nomes de usuário, pastas do computador e endereços eletrônicos não são exibidos na aplicação nem gravados nos arquivos Excel, Word e PDF. O catálogo e o inventário publicados também armazenam somente referências técnicas sanitizadas.

Não havia bases de preços SINAPI/SICRO nas duas planilhas. A hierarquia está implementada e testada, mas essas fontes não aparecem artificialmente nos cenários. Para adicionar uma referência alternativa, é necessário cadastrá-la com fonte, código, unidade, preço, data e proveniência e incluí-la explicitamente como candidata equivalente na regra. O motor não infere equivalência apenas por descrição. Divergências de preço na mesma chave interrompem a importação. Unidades incompatíveis ou ausência de todos os preços interrompem o cálculo, sem gerar total subestimado.

SIEC: junho/2026; provisões: setembro/2026 declarado; anúncio: 13/09/2026. Sem atualização automática por índice. O relatório lista limites de projeto e parcelas provisórias.

## Estrutura

```text
app.py                       interface Streamlit
railbudget/engine.py         função pura calculate(Scenario, regras, catálogo)
railbudget/expressions.py    avaliador aritmético restrito, sem eval
railbudget/exporters.py      Excel, Word e PDFs em memória
railbudget/importer.py       extração reprodutível das duas planilhas
railbudget/build_rules.py    estruturação inicial das memórias extraídas
config/rules.json            seleção, candidatos, expressões e parâmetros
config/coverage.json         destino das 281 linhas das EAPs originais
data/catalog.sqlite         banco de preços com índice por código
data/scope2_prices.json     referência contratual de material rodante
data/inventory.json          inventário das 21 abas e hashes das fontes
data/snapshots.json          fórmulas e valores originais preservados
docs/MAPEAMENTO.md           decisões de consolidação e extrapolação
tests/                      regressões, casos limites, interface e exportação
```

As rotinas de importação/estruturação são módulos de manutenção, sem executável de terminal ou interface alternativa. Não regenere regras sobre alterações manuais sem revisar as diferenças. Alterações de arquivo são recarregadas pelo aplicativo; versões do banco e das regras participam das chaves de cache.

## Validação

Quatro cenários completos do legado fecham com as planilhas manuais: R$ 53.552.530,02 e R$ 80.467.223,28 para elevado simples/duplo; R$ 13.321.596,60 e R$ 20.597.620,85 para superfície simples/dupla. Essa conferência também pode ser executada pela tela **Regras e validação**.

Dois testes adicionais reconciliam os cenários consolidados SIEC com os subtotais e linhas das duas origens, incluindo substituições e harmonização de prazo/geometria. Não são apresentados como um orçamento manual consolidado anteriormente existente. Testes automatizados de desenvolvimento usam pytest; não oferecem interação com o usuário fora do Streamlit.

O Excel exportado inclui preços por PROCV exato, quantidades por fórmulas, caches numéricos para leitura imediata e recálculo no Excel. Alterar modelo ou seleção de grupos deve ser feito no aplicativo e reexportado; o arquivo representa um cenário, não uma segunda aplicação de seleção.


### BDI personalizável

O painel **BDI do orçamento**, junto aos resultados, permite editar **BDI personalizado (%)** e marcar ou desmarcar **Aplicar BDI**. A atualização ocorre ao confirmar o campo com Enter ou sair dele. O percentual escolhido é conservado ao desmarcar a aplicação do BDI. Cada cenário A/B tem seu próprio percentual.

O total, os subtotais dos grupos e os custos por km acompanham a escolha. A participação percentual continua baseada no custo direto. Um eventual centavo de arredondamento é ajustado no último grupo selecionado para que seus subtotais fechem com o consolidado. Excel, Word e PDFs usam o percentual efetivamente aplicado; com a opção desmarcada, o BDI exportado é zero. Alterar o BDI descarta downloads anteriores.
