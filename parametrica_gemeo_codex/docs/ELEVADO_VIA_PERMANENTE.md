# Elevado: desenho do viaduto e custo da via permanente

Registro das melhorias do elevado pedidas em 28/10/2026, com prioridade no custo paramétrico da via permanente em elevado.

Ponto de restauração anterior: branch `backup/pre-elevado-2026-10-28` (main em `8d53516`, após o PR #59). Para desfazer, reverta o PR correspondente ou volte a essa branch.

## 1. Desenho do viaduto

### Onde aparece

1. Aba **Passageiro**, campo **Configuração = Elevado**: no fim do painel "2. Parâmetros estruturais do elevado", o expansor **Desenho do viaduto** (aberto por padrão). Ele é redesenhado a cada alteração de campo, sem precisar atualizar o orçamento.
2. No resultado, dentro de **Síntese estrutural do elevado**, com o número de vãos e apoios efetivamente calculados.

### O que o desenho mostra

| Vista | Elementos | Muda com |
|---|---|---|
| Corte transversal | guarda-corpos, canaletas do tabuleiro, paralastro, lastro, dormentes, fixações, trilhos, contratrilhos, laje de distribuição, vigas, travessa, pilar, descida de drenagem, bloco e estacas | via singela/dupla, largura do tabuleiro, altura, tipologia do tabuleiro, tipologia dos pilares, estacas por apoio, diâmetro e profundidade |
| Elevação longitudinal | 2 a 4 vãos típicos com tabuleiro, via, pilares, blocos, estacas e descidas | vão (distância entre pilares) e altura |

Cores: via permanente em vermelho, laranja e amarelo do tema (`#b8322a`, `#e2712a`, `#f4b63f`); drenagem em azul; estrutura em tons neutros.

### Regras do desenho

- É **esquemático e sem escala**: a largura é desenhada até 30 px/m (limitada para caber 20 m) e a altura do pilar cresce com a altura real entre 70 e 200 px. As cotas escritas são sempre os valores reais do cenário.
- Tipologia do tabuleiro: "Vigas pré-moldadas com laje" desenha vigas I (3 na singela, 5 na dupla); "Viga U" desenha uma calha por via; as duas "Viga-caixão" desenham uma seção caixão; "Misto aço-concreto" desenha vigas metálicas.
- Tipologia dos pilares: circular (com sombreamento), retangular, pilar-parede (largo) e pórtico (dois pilares com travessa).
- Estacas: até 8 desenhadas no corte (metade das estacas do apoio quando há 4 ou mais, por ser uma vista); o texto informa a quantidade real, o diâmetro e a profundidade.
- Com trechos homogêneos, o desenho usa o trecho mais extenso.
- Só exibição: nenhum cálculo, preço, regra ou chave de `config/rules.json` foi alterado.

### Código e testes

- `railbudget/elevated_drawing.py`: `drawing_parameters(cenário, elevado)` monta os parâmetros e `elevated_svg(parâmetros)` devolve o SVG.
- `app.py`: expansor no formulário e troca do esquema antigo no resultado.
- `railbudget/interface.py`: removido o CSS `.elevated-scheme`/`.scheme-*`, que não é mais usado.
- Testes: `tests/test_elevated_drawing.py` (SVG válido, cotas, mudança com vias/altura/vão/tipologias, trechos) e `tests/test_app.py` (desenho no formulário, atualização ao mudar a altura e desenho no resultado).

## 2. Custo paramétrico da via permanente no elevado

### Onde aparece

Resultado do orçamento de Passageiro com Configuração = Elevado, logo abaixo da "Síntese estrutural do elevado": bloco **Via permanente no elevado**.

### Componentes e itens do orçamento que entram em cada um

Nenhum preço novo: o bloco soma itens que já estão no orçamento, pelos rótulos e grupos abaixo (com trechos homogêneos, o prefixo "Trecho · " é ignorado).

| Componente | Grupo | Itens (rótulo da aplicação) |
|---|---|---|
| Trilhos | 1 Via permanente | Trilhos |
| Fixações | 1 Via permanente | Fixações (três itens) |
| Dormentes | 1 Via permanente | Dormentes |
| Lastro e paralastro | 1 Via permanente | Lastro, Transporte do lastro, Paralastro |
| Montagem, soldagem e geometria | 1 Via permanente | Montagem, Regularização, Geometria final, Soldagem, Controle de soldas |
| Contratrilhos de segurança | 1 Via permanente | Contratrilhos de segurança, Montagem dos contratrilhos |
| AMVs | 5 AMVs | grupo inteiro |
| Drenagem do tabuleiro | 3 Drenagem | Canaletas no tabuleiro, Descidas do tabuleiro DN100, Caixas nos pés dos pilares |

Ficam fora (são estrutura ou proteção, não via): fundações, pilares, tabuleiro, guarda-corpos, fechamento, canteiro, administração e provisões.

### Indicadores

- **Custo direto** da via permanente (sem BDI) e o mesmo valor com o BDI do cenário.
- **R$/km de via** = custo ÷ (km de corredor × nº de vias).
- **R$/m de viaduto** = custo ÷ (km de corredor × 1.000).
- **Parte do custo direto** = via permanente ÷ custo direto do recorte selecionado.
- O bloco respeita os grupos marcados: um grupo desmarcado zera o componente correspondente.

### Sensibilidade

Cada ponto recalcula o orçamento do elevado (`calculate_elevated`) mudando só uma variável:

- Vão: 10, 15, 20, 25, 30, 35, 40 e 45 m.
- Altura dos pilares: 3, 6, 9, 12, 15, 20, 25 e 30 m.
- Tipologia do tabuleiro: as cinco opções do formulário.
- Via: singela e dupla (com a largura de tabuleiro informada para cada uma).

Para cada ponto: via permanente (R$/m de viaduto), estrutura do viaduto (fundações + pilares + tabuleiro, R$/m) e via permanente (R$/km de via). Com trechos homogêneos, o vão ou a altura testados valem para todos os trechos. São 23 recálculos (menos de meio segundo), guardados na sessão até o cenário mudar.

Leitura no cenário padrão (1 km, via singela, vão 20 m, altura 8 m): via permanente ≈ R$ 6.777/m e estrutura ≈ R$ 35.669/m. A via quase não muda com vão e altura (só a drenagem do tabuleiro depende de apoios e altura); a estrutura cai de R$ 53.855/m (vão 10 m) para R$ 25.848/m (vão 45 m) e sobe de R$ 31.865/m (altura 3 m) para R$ 52.405/m (altura 30 m). Na via dupla, o custo por metro sobe, mas o custo por km de via cai (R$ 5,65 milhões contra R$ 6,78 milhões), porque paralastro e estrutura são compartilhados.

### Limitação declarada

A base SIEC só tem via sobre lastro. "Tipo de via" foi tratado como tipologia do tabuleiro e nº de vias. Via em laje (sem lastro) exigiria uma composição de preço nova, a ser aprovada antes de entrar no cálculo.

### Código e testes

- `railbudget/elevated_track.py`: `track_breakdown(resultado)` e `track_sensitivity(cenário, regras, catálogo, trechos, grupos)`.
- `app.py`: `render_elevated_track_cost` e `track_sensitivity_chart` (cores validadas para daltonismo: via `#b8322a`, estrutura `#2f74b5`).
- Testes: `tests/test_elevated_track.py` (soma confere item a item, AMVs = grupo 5, divisões por km de via e metro, recorte de grupos, varredura de vão/altura/tabuleiro/vias, trechos) e `tests/test_app.py` (bloco e sensibilidade na tela).
