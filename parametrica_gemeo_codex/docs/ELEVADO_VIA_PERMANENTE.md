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
