# Registro de validação — 13/09/2026

Versão das regras: 1.0.0. Interface Streamlit 1.63.0.

## Dados e cálculo

- 21 abas inventariadas nas duas planilhas; hashes e proveniência preservados.
- 13.260 referências únicas no SQLite, incluindo 13.176 SIEC; duplicidades entre origens eliminadas sem perder rastreabilidade.
- Cobertura documentada das 281 linhas de EAP: seleção, substituição por complemento equivalente ou alternativa de modelo.
- Quatro cenários completos do legado reproduzidos, com conferência de quantidades e totais das linhas.

| Cenário legado de 1 km | Total com BDI |
|---|---:|
| Elevado simples | R$ 53.552.530,02 |
| Elevado duplo | R$ 80.467.223,28 |
| Superfície simples | R$ 13.321.596,60 |
| Superfície dupla | R$ 20.597.620,85 |

Dois casos adicionais reconciliam a consolidação SIEC com subtotais das duas origens após retirar duplicidades e harmonizar prazo e geometria. Não existia orçamento manual prévio dessa consolidação. A referência padrão consolidada de superfície simples resulta em R$ 9.929.071,15, com 60 linhas SIEC.

## Verificações executadas

24 testes automatizados aprovados: motor, regressões dos cenários, hierarquia de fontes, ausência de preços, unidades, entradas inválidas, distribuição dos AMVs, expressões restritas, formulários, comparação e quatro exportações.

No navegador, foram conferidos o cálculo padrão, os botões dos quatro downloads e a comparação entre via simples e dupla. No Excel instalado, o recálculo completo reproduziu o total do motor; alterar um preço na aba de base modificou o orçamento, sem erros nas fórmulas verificadas. A alteração foi descartada após o teste.

As páginas dos PDFs de orçamento e memória foram renderizadas e inspecionadas. As oito páginas do relatório Word foram conferidas por renderização antes do último ajuste, que removeu a borda decorativa do título. A estrutura do DOCX ajustado passou nos testes; a nova renderização no Word ficou bloqueada na conversão e permanece pendente. Isso não afeta a geração dos downloads, que não utiliza o Office. Os PDFs são documentos equivalentes produzidos pelo mesmo resultado, com paginação própria.

## Alcance

A validação confirma a reprodução das referências recebidas e a consistência do software. As extrapolações para via dupla SIEC estão identificadas no mapeamento. As bases recebidas não contêm tabelas SINAPI/SICRO; a hierarquia para essas fontes foi testada com dados de teste, sem cadastrar preços fictícios no banco entregue. Preços provisórios do legado permanecem explicitamente separados de SIEC e mercado.
