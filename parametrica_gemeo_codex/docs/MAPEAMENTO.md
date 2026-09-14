# Mapeamento das duas origens

Inventário completo de abas, dimensões, fórmulas e SHA-256: `data/inventory.json`.
Valores armazenados e fórmulas originais de todas as abas: `data/snapshots.json`.
Os arquivos de origem não são alterados. A aplicação opera com sua cópia estruturada local.

## Estrutura encontrada antes da implementação

- VPCODEX2026: 8 abas; EAPs Superfície (42 linhas) e Elevado (59 linhas), colunas A:L; quantidade I, preço J, direto K. Busca IF/PROCV exata em SIEC_SERVIÇOS e SIEC_INSUMOS. Premissas B5:B31; BDI calculado em B34. Via lastreada nos dois cenários, AMV TR57 nº14, envelope 50 m, vão elevado de 20 m. Apenas via simples previamente orçada.
- CODEX_PARAMETRICO_GERAL: 13 abas; 180 linhas distribuídas entre os seis grupos e alternativas. Quantidade I, preço J, direto K. Abas SIEC completas e iguais às da primeira pasta; preços provisórios em Base Parte 1; anúncio Carelli em Mercado e pendências. Via de superfície lastreada; elevado em placa; AMV TR57 nº9, envelope 40 m, vão de 30 m. Quatro cenários previamente orçados.
- SIEC: 10.157 serviços e 3.019 insumos, junho/2026. Registros 'sob consulta' permanecem sem preço; não recebem zero.
- Não há tabelas SINAPI/SICRO de preços nestas duas planilhas. O motor aceita candidatos explicitamente equivalentes e prioriza SIEC → SINAPI → SICRO → Mercado. Não inventa equivalências nem usa o nº14 como preço do nº9.

## Consolidação de escopo

Padrão SIEC: reutiliza via, infraestrutura e AMV nº14 do VPCODEX2026. Topografia, drenagem e infraestrutura de cabos anteriores são substituídas integralmente pelos grupos 2, 3 e 6 da Parte 2. Vedação da faixa é adicional; guarda-corpos e fechamento do tabuleiro são proteção do elevado e permanecem no grupo 1 mesmo quando 'Nenhuma' vedação é selecionada.

O grupo 1 e AMV nº9 da Parte 2 formam o perfil alternativo **Legado Parte 2**, sem mistura com o modelo SIEC. Todos os 281 registros das EAPs originais têm destino registrado em `config/coverage.json`: utilizados, substituídos ou disponíveis no perfil alternativo. Rateios informativos de AMVs não são somados novamente.

Comparações de modelos diferentes representam também mudança de escopo: lastro/placa, AMV e geometria estrutural. O aplicativo mostra o modelo usado em cada resultado e exportação.

## Extrapolação

Quantidades passam a depender da extensão e AMVs efetivamente informados, preservando a referência de 1 km. Fundações arredondam vãos/apoios, dormentes arredondam por linha e caixas incluem extremos. AMVs são quantidade total do corredor, distribuídos entre linhas (diferença máxima de uma unidade); envelope não pode consumir toda a via.

Via dupla SIEC é uma extrapolação nova, identificada como tal: entrevia 4 m, plataforma/tabuleiro compartilhados mais largos, fatores de 1,5 para fundações e mesoestrutura e 1,25 para instalação/gestão. Esses fatores são configuráveis e não constituem dimensionamento. Custos fixos de campanhas e mobilização não variam automaticamente com km. Prazo permanece o da referência até alteração explícita no formulário.

O legado preserva seus fatores e memórias. Há valores fixos/vb que só podem ser refinados com projeto. Preços não são reajustados automaticamente entre datas-base. BDI é editável e parte da taxa herdada, não de validação tributária nova.
