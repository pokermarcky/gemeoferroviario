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

## Ferrovia de carga: carga por eixo

Arquivo de premissas: `config/freight_axle.json`. Cálculo: `railbudget/freight.py`. **Preços e códigos vêm da SIEC junho/2026; os valores geométricos abaixo são premissas preliminares a validar em projeto e não vêm da base SIEC.** As ISF-212 (lastro e sublastro) e ISF-213 (trilhos e dormentes) do DNIT foram usadas como roteiro do que precisa ser dimensionado, não como fonte dos números.

Geometria implícita na referência SIEC de superfície (já usada em passageiros e mantida intacta): seção de lastro com 0,50 m de altura (0,30 m sob dormente de 0,20 m), topo de 3,60 m, talude 1,5:1 e base de 5,10 m; plataforma de 6,0 m (banquetas de 0,45 m); sublastro de 20 cm; dormentes a cada 0,60 m (1.667/km).

| Faixa | Trilho SIEC | Dormente, montagem e solda SIEC | Espaçamento | Lastro sob dormente | Sublastro | Plataforma resultante |
|---|---|---|---|---|---|---|
| 16 a 20 t/eixo | TR-57 IH (SIEC-03.04.01.100.08), 57 kg/m | TR-57 (…100.01, 03.03.04.100.01, …100.30) | 0,60 m | 0,30 m | 0,20 m | 6,00 m |
| acima de 20 até 25 t/eixo | UIC 60 (SIEC-03.04.01.100.10), 60 kg/m | UIC 60 (…100.03, 03.03.04.100.03, …100.32) | 0,60 m | 0,35 m | 0,20 m | 6,15 m |
| acima de 25 t/eixo | bloqueado | — | — | — | — | — |

Acima de 25 t/eixo a prática usual pede TR-68; a SIEC tem montagem, dormente e solda TR-68, mas não tem preço de fornecimento do trilho TR-68. O aplicativo recusa o cálculo em vez de usar outro perfil.

Regras de redimensionamento (itens `vp:Superfície:*`; identificadores e `rules.json` não mudam):

- Trilho (26): `2 × via corrida × kg/m ÷ 1000 × 1,02`.
- Dormentes (27) e fixações (28 a 30): mesma regra de arredondamento por via e AMV do motor, com o espaçamento informado; 4 grampos, 4 isoladores e 2 palmilhas por dormente.
- Lastro (31) e transporte (32): seção trapezoidal `H × (3,60 + 1,5 × H)`, com `H = lastro sob dormente + 0,20`, menos o volume dos dormentes, mais os termos de AMV da referência, 10% de perdas.
- Plataforma: `largura = 3,60 + 2 × 1,5 × H + 2 × 0,45`. Limpeza, corte, carga, transporte e aterro (19 a 23) são multiplicados por `(largura + 4 × (vias − 1)) ÷ (6 + 4 × (vias − 1))`; compactação (24) usa a nova área; sublastro (25) = área × espessura.
- Montagem (33) e solda (36) trocam para o código do perfil. AMVs, drenagem e vedação seguem a referência SIEC.

Com as premissas iniciais, 20 t/eixo reproduz exatamente os quantitativos e o custo direto da referência SIEC de superfície. Espaçamento (0,50 a 0,65 m), lastro (0,25 a 0,45 m) e sublastro (0,20 a 0,40 m) são editáveis no formulário e aparecem na aba Premissas do Excel.

Orçamentos de carga salvos antes desta versão reabrem com a geometria da referência (0,60/0,30/0,20 m), que foi a usada no cálculo original. O resultado salvo não é alterado.

**Fora do total, listados separadamente:** locomotivas e vagões (a SIEC tem custo horário de operação, não preço de aquisição), pátios de cruzamento ou terminais, pontes e viadutos (a referência do elevado é de passageiros) e passagens em nível. As quantidades informadas aparecem no resultado, na aba Resumo do Excel e nas premissas, sempre como "Não precificado · fora do total". Nenhum preço é atribuído.
