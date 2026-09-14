# Gêmeo digital de orçamentação ferroviária — Codex

Aplicação **Streamlit** que consolida VPCODEX2026 e CODEX_PARAMETRICO_GERAL. Calcula EAP, custo total com BDI e custos por km de corredor e de linha. Inclui comparação lado a lado, pesquisa das bases e downloads Excel, Word e dois PDFs.

## Uso

No ambiente Python do projeto, a única forma de uso da aplicação é:

```powershell
streamlit run app.py
```

Abra o endereço local mostrado pelo Streamlit. Preencha o formulário e clique em **Calcular Orçamento**. Para baixar documentos, clique em **Preparar arquivos para download** e escolha Excel, Word, PDF do orçamento ou PDF do relatório. As abas **Comparar cenários**, **Base de dados** e **Regras e validação** concentram as demais funções. Não há versão CLI ou notebook para o usuário.

O resultado mostrado pertence ao último formulário enviado, identificado no cabeçalho. Alterações ainda não enviadas não modificam o orçamento. Downloads sempre usam o cenário calculado, não o formulário pendente. Ao calcular novamente, os downloads anteriores são descartados. Resultados de sessão não persistem ao encerrar o servidor.

### Preparação do ambiente

Python 3.12 recomendado. O ambiente `.venv` já foi preparado nesta máquina. Para ativá-lo no PowerShell, execute `.\.venv\Scripts\Activate.ps1` dentro da pasta do projeto. Em outra instalação, crie um ambiente Python e instale as dependências de `requirements.txt` com pip. Essa preparação não é um modo alternativo de uso da aplicação.

O servidor está configurado apenas em `127.0.0.1`. Não depende das pastas originais após a extração; o banco local, as regras e a documentação acompanham o projeto. PDFs usam ReportLab, sem necessidade de Office ou LibreOffice. São versões equivalentes do mesmo resultado, com paginação própria, e não impressões idênticas do Excel/Word.

## Modelos

- **SIEC (padrão):** via lastreada e AMV nº14 do VPCODEX2026; complementos gerais da Parte 2. Remove topografia, drenagem e dutos anteriores antes de inserir os substitutos. Preserva proteções do tabuleiro como grupo 1; vedação da faixa é outra função.
- **Legado Parte 2:** reproduz os quatro orçamentos anteriores, incluindo elevado em placa e AMV nº9 com preços provisórios. Não atribui o preço nº14 ao nº9.
- **Via dupla SIEC:** extrapolação explícita de plataforma compartilhada e fatores de gestão/fundações em `config/rules.json`; não existe planilha manual prévia dessa combinação. Não equivale a dimensionamento estrutural.
- AMVs são quantidade **total**, não por linha nem por km. Envelopes são abatidos da via corrida e distribuídos entre linhas. Prazo 0 utiliza a referência do modelo; é possível informar prazo específico.

## Rastreabilidade e dados

`data/catalog.sqlite` tem 13.260 referências únicas: 13.176 SIEC, 83 registros herdados e 1 anúncio de mercado. Os 83 registros incluem rateios informativos não somados ao orçamento. Linhas sem preço permanecem `NULL`, nunca zero. Fontes SIEC duplicadas entre as duas planilhas foram unificadas, preservando ambas as proveniências.

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
