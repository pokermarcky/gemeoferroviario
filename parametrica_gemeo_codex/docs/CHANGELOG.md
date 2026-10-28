# Histórico de alterações

Ponto de restauração anterior a estas alterações: branch `backup/estavel-2026-10-23` (commit `08fdea8`).

## 2026-10-28 — Desenho do viaduto nos arquivos baixados (elevado, item 3)

- Ao baixar um orçamento com elevado, o **Excel**, o **Word**, o **PDF resumido** e o **PDF detalhado** passam a trazer o desenho do viaduto (corte transversal e elevação longitudinal) e a tabela **Via permanente no elevado** (custo por componente, R$/km de via, R$/m de viaduto, participação e total com BDI). No Excel, o desenho fica numa aba nova "Desenho do elevado", no fim da pasta.
- A imagem é gerada a partir do mesmo SVG da tela, com Pillow e as fontes do reportlab, sem dependência nova. As cores vêm do desenho da tela, então mudanças de tema chegam aos arquivos.
- Só conteúdo dos arquivos: nenhum cálculo, preço ou regra muda, e o limite de download da demonstração continua igual. Cenários sem elevado não mudam.
- Novo módulo `railbudget/drawing_image.py`; `railbudget/exporters.py` inclui as seções. Documentação em `docs/ELEVADO_VIA_PERMANENTE.md` (seção 3).
- Testes: 25 novos em `tests/test_desenho_downloads.py`.
## 2026-10-28 — Tons mais sóbrios no lugar do laranja vivo

Ponto de restauração: branch `backup/pre-tema-sobrio-2026-10-28` (main após o PR #61, commit `a429cdc`).

- A pedido do Marcelo, o laranja e o amarelo vivos do tema foram trocados por tons sóbrios da mesma família: terracota `#a0614c` no lugar de `#e2712a` e ocre suave `#c9ad80` no lugar de `#f4b63f`. O vermelho principal `#b8322a` continua.
- Vale para o gráfico de participação por grupo (`#a3483a`), o céu da ilustração do topo, o degradê dos destaques (cabeçalho do resultado, indicadores, cartão "Seu espaço", abas selecionadas), os fundos creme (menos amarelados), as bordas e o contorno de foco, e para o desenho do viaduto (dormentes, lastro e paralastro).
- Só aparência: nenhum cálculo, preço, regra ou dado muda.
- Testes: 126 antes, 129 depois (`tests/test_tema_sobrio.py`).

## 2026-10-28 — Custo da via permanente no elevado por componente (elevado, item 2)

- Novo bloco **Via permanente no elevado** no resultado do elevado (Passageiro): custo direto da via sobre o viaduto separado em Trilhos, Fixações, Dormentes, Lastro e paralastro, Montagem/soldagem/geometria, Contratrilhos de segurança, AMVs e Drenagem do tabuleiro, com **R$/km de via**, **R$/m de viaduto**, participação de cada componente, valor com BDI e a parte da via no custo direto. Gráfico de barras por componente.
- **Sensibilidade**: gráficos do custo por metro de viaduto (via permanente × estrutura) variando o vão (10 a 45 m) e a altura dos pilares (3 a 30 m), e tabela por tipologia do tabuleiro e via singela/dupla. Cada ponto recalcula o orçamento mudando só uma variável. Resultado no cenário padrão: a via permanente fica em torno de R$ 6.800/m e quase não muda com vão e altura; a estrutura vai de R$ 54 mil/m (vão 10 m) a R$ 26 mil/m (vão 45 m).
- Só agrupa e divide itens que já existiam: nenhum preço, quantidade, regra ou chave de `rules.json` muda. Respeita os grupos marcados (sem o grupo de AMVs, a linha AMVs fica zerada). "Tipo de via" ficou como tipologia do tabuleiro e nº de vias, porque a base SIEC só tem via sobre lastro; via em laje exigiria uma composição de preço nova.
- Novo módulo `railbudget/elevated_track.py`; `app.py` ganha `render_elevated_track_cost`. Documentação em `docs/ELEVADO_VIA_PERMANENTE.md`.
- Testes: 121 antes, 126 depois (`tests/test_elevated_track.py` e `tests/test_app.py`).

## 2026-10-28 — Desenho do viaduto no elevado (elevado, item 1)

Ponto de restauração destas alterações do elevado: branch `backup/pre-elevado-2026-10-28` (main após o PR #59, commit `8d53516`).

- Novo painel **Desenho do viaduto** no formulário do elevado (Passageiro → Configuração "Elevado"): corte transversal e elevação longitudinal em SVG, nas cores do tema. O desenho muda na hora com via singela/dupla, largura do tabuleiro, altura dos pilares, vão, estacas por apoio, diâmetro, profundidade, tipologia do tabuleiro (vigas, viga U, caixão, misto) e tipologia dos pilares (circular, retangular, parede, pórtico).
- A via permanente aparece em destaque (trilhos, contratrilhos, dormentes e fixações, lastro e paralastro), com legenda; drenagem do tabuleiro em azul e estrutura em tons neutros.
- O mesmo desenho substitui o esquema simples da "Síntese estrutural do elevado" no resultado, agora com o número de vãos e apoios calculados. Com trechos homogêneos, mostra o trecho mais extenso.
- Desenho esquemático, sem escala; as cotas escritas são os valores do cenário. Só exibição: nenhum cálculo, preço, regra ou chave de `rules.json` muda.
- Novo módulo `railbudget/elevated_drawing.py`; CSS antigo do esquema (`.elevated-scheme`) removido de `interface.py`. Documentação em `docs/ELEVADO_VIA_PERMANENTE.md`.
- Testes: 117 antes, 121 depois (`tests/test_elevated_drawing.py` e `tests/test_app.py`).

## 2026-10-28 — Comparar dois cenários lado a lado (melhoria 5)

- Novo bloco **Comparar cenários** no resultado de Passageiro, Carga e Shortline: "Fixar como cenário A" guarda o resultado exibido; depois de alterar o cenário e selecionar Atualizar orçamento, a tela mostra A, B, a diferença em reais e a variação (%) por grupo e nos indicadores (direto, BDI, total, por km, frota e infraestrutura por km), com uma frase-resumo ("Cenário B custa R$ X a mais que o A").
- Botões para fixar o atual como novo A, limpar e baixar a comparação em Excel (contas com download ilimitado). O cenário A fica só na sessão do navegador.
- Funcionalidade aditiva: novo módulo `railbudget/comparison.py`, que apenas lê resultados já calculados. Nenhum cálculo, regra, preço ou dado salvo muda. O VLT não tem comparação nesta versão.
- Testes: 113 antes, 117 depois (`tests/test_comparison.py` e `tests/test_app.py`).

## 2026-10-28 — Documentação atualizada e código sem uso removido (melhoria 4)

- `README.md`: quatro modalidades, botão **Atualizar orçamento** (não "Calcular"), downloads em Excel/PDF/Word, indicadores por km, subterrâneo preliminar (antes dizia que não orçava), sem estações no formulário, bases de referência gravadas em `.runtime/` (somem num *Reboot app*), carteira no Supabase, Excel com valores fixos e estrutura de módulos atual.
- `docs/PLANO_APRIMORAMENTOS.md`: situação em 28/10 (etapas 1–3 concluídas, 4–5 pendentes), Subterrâneo e Shortline com orçamento, Excel sem PROCV.
- `docs/VALIDACAO.md`: nota no topo explicando o que mudou desde o registro de 13/09; o registro histórico foi preservado.
- `AI_MEMORY.md`: contagem de testes, URL publicada, CHANGELOG, branches de restauração e o alerta sobre `RAILPARAMETRIC_TEST_MODE`.
- Removidos `railbudget/stations.py` e `railbudget/realistic_scene.py`, que não eram importados por nenhum módulo nem teste. Continuam no histórico do Git e na branch `backup/pre-melhorias-2026-10-28`.
- Novo teste garante que o README só cita módulos existentes. Testes: 112 antes, 113 depois. Sem mudança de cálculo, preços ou dados.

## 2026-10-28 — Resultado legível de relance (melhoria 3)

- "Participação por grupo": a tabela mostra só os grupos marcados, com a coluna **Participação** (%) e altura ajustada ao número de linhas (antes ficava fixa em 320 px e escondia Material rodante, o maior item do passageiro). Na carga, os grupos desmarcados deixam de aparecer como R$ 0,00.
- Gráfico de barras ordenado do maior para o menor, eixo em **R$ milhões** com vírgula decimal e ponto de milhar, e valor exato ao passar o mouse. Mesma cor do tema (#c4421f). O VLT usa o mesmo gráfico.
- BDI exibido com duas casas ("26,30%" em vez de "26,300000%").
- Shortline: ao alterar um campo, o resultado anterior continua visível com o aviso para atualizar, como nas outras abas (antes a tela de resultado sumia).
- Sem mudança de cálculo, preços ou dados. Testes: 111 antes, 112 depois.

## 2026-10-28 — Downloads em PDF e Word; limite da demonstração no VLT (melhoria 2)

- Passageiro, Carga e Shortline passam a oferecer, além do Excel, **PDF resumido**, **PDF detalhado** e **relatório Word**. Os geradores (`make_pdf`, `make_word` em `exporters.py`) já existiam e eram testados, mas não tinham botão. Os arquivos refletem o recorte exibido (grupos marcados e BDI).
- O botão do Excel passa a se chamar "Excel" dentro do bloco "Baixar orçamento"; a chave interna `<aba>_excel` não muda.
- Demonstração: continua com um único download por sessão, agora em qualquer formato. O Excel do VLT não consumia esse limite e foi corrigido; o arquivo do VLT também passou a ser guardado em cache em vez de regenerado a cada interação.
- Sem mudança de cálculo, preços ou dados. Testes: 110 antes, 111 depois.

## 2026-10-28 — Indicadores por km corretos (melhoria 1)

Ponto de restauração destas melhorias: branch `backup/pre-melhorias-2026-10-28` (main após o PR #54/#53).

- Shortline: o custo por km de via passa a acompanhar os grupos marcados e o BDI. Antes vinha do orçamento completo (com sinalização e BDI, mesmo desmarcados): no cenário padrão a tela mostrava R$ 7.099.006,38; o valor correto é R$ 7.000.316,78 com BDI. O terceiro cartão da Shortline agora é "Por km de via" (principal + desvios + pátio) em vez de "Por km de linha", que repetia o valor por km de corredor.
- Passageiro: quando há material rodante, dois cartões novos mostram a frota incluída no total e a **infraestrutura por km** sem a frota. Os cartões existentes não mudam.
- Excel (aba Resumo): linhas novas "R$/km de via" (Shortline) e "Frota" / "R$/km corredor sem frota" (quando há frota).
- `select_groups` (engine.py) ganha chaves aditivas `fleet_total`, `per_km_without_fleet` e `per_track_km`; nenhum total, regra, preço ou dado salvo muda.
- Testes: 108 antes, 110 depois.

## 2026-10-23 — Aba Shortline (PR #53)

- Aba **Shortline** preenchida: ferrovia de carga curta em via singela, superfície, tração diesel. Linha principal pelo motor de carga (`calculate_freight`, carga por eixo de 16 a 25 t com TR-57 ou UIC 60), desvios de cruzamento e vias de pátio com as mesmas composições SIEC da via corrida (sem repetir canteiro, sondagens e administração local), 2 AMVs por desvio + AMVs de pátio, BDI editável, Excel e reabertura de projetos salvos.
- Passagens em nível, locomotivas, vagões, terminais e obras de arte especiais ficam registrados como escopo pendente, fora do total. Nenhum preço novo.
- Novo módulo `railbudget/shortline.py`; ajustes aditivos em `app.py`, `user_workspace.py`, `exporters.py` (premissas extras) e `localization.py` (prefixo "desvios e pátio"). Sem mudança em `engine.py`, `freight.py`, `data/` ou `config/`; Passageiro, Carga e VLT inalterados.
- Testes: 100 antes, 108 depois (`tests/test_shortline.py` e `tests/test_app.py`).

## 2026-10-23 — Auditoria de segurança, persistência, elevado e Excel

- Relatório completo em `docs/AUDITORIA.md`. Nenhum secret real no repositório nem no histórico.
- Testes novos: persistência da carteira com Supabase simulado e SQLite (`tests/test_persistencia.py`), conferência independente do elevado (`tests/test_elevado_independente.py`) e integridade do Excel (`tests/test_excel_integridade.py`).
- Excel: textos da EAP e das abas de grupo deixam de citar PROCV/vínculos, pois o arquivo traz valores fixos desde o PR #28.
- Removidos do Git os `.pyc` de `railbudget/__pycache__/`.
- Sem mudança de cálculo, preços ou dados. Testes: 85 antes, 100 depois.

## 2026-10-23 — Carga por eixo redimensiona a via de carga

- `config/freight_axle.json` (novo) e `railbudget/freight.py`: carga por eixo de 16 a 25 t em duas faixas (TR-57 até 20 t; UIC 60 acima). Trilho, dormentes, fixações, lastro, transporte de brita, sublastro e plataforma passam a ser redimensionados; dormente e solda usam o código SIEC do perfil UIC 60. Acima de 25 t o cálculo é recusado (sem preço SIEC do trilho TR-68).
- Formulário de carga: carga por eixo numérica, painel "Premissas técnicas da via de carga (a validar)" e campos de pátios, pontes/viadutos e passagens em nível. Esses itens e a frota ficam em lista separada, fora do total, no resultado e no Excel.
- Impacto: 20 t/eixo mantém exatamente o valor anterior. 25 t/eixo sobe cerca de 1,2% a 1,4% (lastro de 35 cm, plataforma de 6,15 m e solda UIC 60). Passageiros, VLT, identificadores do motor e orçamentos salvos não mudam; orçamentos de carga antigos reabrem com a geometria original.
- Documentação em `docs/MAPEAMENTO.md` (seção "Ferrovia de carga: carga por eixo") e `README.md`. Testes: 78 antes, 85 depois.

## 2026-10-23 — Memórias de cálculo em português (PR #44)

- `railbudget/localization.py`: `ROUNDUP`/`ROUNDDOWN` aparecem como "arredondar para cima/baixo" sem o argumento de casas; `PI()` aparece como π; decimais com vírgula, argumentos separados por ponto e vírgula e operadores × e ÷.
- Origem das regras (`vp`, `p2`, `Ajuste 2`, `subterraneo`) exibida por extenso no Excel, Word e PDF (`origem_legivel`).
- Somente apresentação: expressões executáveis, chaves de `config/rules.json`, fórmulas do Excel e orçamentos salvos não mudam.
- Testes: 75 antes, 78 depois (`tests/test_localization.py`).
