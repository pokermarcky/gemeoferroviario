# Parametric Rails

O cabeçalho exibe uma cena panorâmica de ferrovia de carga, trem de passageiros e VLT. A imagem otimizada está em `assets/hero-trens-vermelhos-v1.webp` e acompanha a aplicação publicada.

Aplicação Streamlit para orçamentos paramétricos ferroviários, publicada em https://railparametric.streamlit.app/. Há quatro modalidades: **Ferrovia de passageiro** (base SIEC • lastro / AMV nº 14 em superfície, elevado ou subterrâneo preliminar), **Ferrovia de carga** (infraestrutura em superfície), **VLT** (edital do Ramal VLT Aeroporto - Castelão) e **Shortline** (carga curta em via singela). Todas apresentam EAP, BDI editável, custos por km e downloads do orçamento.

## Uso

```powershell
streamlit run app.py
```

Abra **ORÇAMENTOS → Ferrovia de passageiro**, informe a extensão, configuração e quantidade de vias, escolha os grupos de serviço e clique em **Atualizar orçamento**. O bloco **Baixar orçamento** entrega o cenário calculado com os grupos atualmente selecionados em **Excel**, **PDF resumido**, **PDF detalhado** e **Word** (Passageiro, Carga e Shortline; o VLT oferece Excel). As abas **Resumo geral** e **Detalhamento por grupo** mostram o resultado na página: a tabela de participação lista só os grupos marcados e o gráfico ordena do maior para o menor, em R$ milhões. EAP completa e composições detalhadas ficam em painéis recolhíveis.

No fim do resultado, **Comparar cenários** fixa o resultado atual como cenário A; depois de mudar o cenário e atualizar, mostra a diferença por grupo e nos indicadores, com download em Excel.

Os indicadores mostram total, custo por km de corredor e por km de linha. Quando há material rodante, aparecem também a **frota** incluída no total e a **infraestrutura por km** sem a frota, que é o número comparável a referências de custo por km de via. Na Shortline, o terceiro indicador é o custo por **km de via** (linha principal + desvios + pátio); todos acompanham os grupos marcados e o BDI.

**Banco de dutos** aparece entre os grupos de superfície e corresponde ao banco subterrâneo de seis dutos. Em elevado, o mesmo grupo passa a **Canaletas e passa-fios**, conforme as composições aplicáveis. O controle de prazo foi retirado do formulário; o cálculo conserva o prazo de referência interno do modelo para os quantitativos que dependem dele.

A opção **Subterrâneo** produz uma estimativa preliminar por equivalência SIEC (`railbudget/underground.py`), com premissa de um tubo circular de 10,00 m por via e aviso explícito na tela: não substitui projeto geotécnico, estrutural, hidráulico, de ventilação ou de segurança. Estações de passageiros não fazem parte do formulário: a base não tem composição pronta do edifício completo.

Em **Ferrovia de carga**, informe extensão, vias e escopo de infraestrutura. O cenário inicial desativa banco de dutos, rede aérea, sinalização e material rodante. AMVs são opcionais. Locomotivas e vagões aparecem como quantidades de escopo, sem preço de aquisição: a SIEC contém custos horários de operação desses veículos, que não podem representar sua compra. A carga por eixo (16 a 25 t) escolhe o trilho (TR-57 até 20 t, UIC 60 acima) e redimensiona dormentes, fixações, lastro, sublastro e plataforma por premissas editáveis, documentadas em `docs/MAPEAMENTO.md` e a validar em projeto. AMVs, drenagem e vedação seguem a referência SIEC. Pátios, terminais, obras de arte, passagens em nível e frota podem ser informados, mas aparecem em lista separada, fora do total; não compare o valor por km de carga e passageiros como se os escopos fossem idênticos.

Em **Shortline**, a aba orça uma ferrovia de carga curta em via singela, em superfície e com tração diesel. Informe a extensão da linha principal, a carga por eixo (16 a 25 t, com TR-57 até 20 t e UIC 60 acima, como na ferrovia de carga), os desvios de cruzamento com seu comprimento útil, as vias de pátio e os AMVs de pátio. Cada desvio soma dois AMVs nº 14. A via de desvios e pátio usa as mesmas composições SIEC da via corrida, sem repetir canteiro, sondagens e administração local. Drenagem, vedação e topografia acompanham apenas a linha principal, e a sinalização começa desmarcada. Passagens em nível, locomotivas, vagões, terminais e obras de arte especiais ficam registrados como escopo pendente, fora do total, porque a SIEC não traz preço de aquisição ou composição completa para eles. O comprimento dos desvios, o leiaute de pátio e o número de AMVs são premissas a validar em projeto. O cálculo está em `railbudget/shortline.py` e reaproveita o motor de carga sem alterá-lo.

Na aba **BASES DE REFERÊNCIA** há uma área por fonte (SIEC, SINAPI, SIURB, SICRO) e por tipo (Insumos ou Serviços). Todos consultam as bases; só o administrador root envia uma nova tabela (CSV, XLS, XLSX ou XLSM, até 200 MB) com a data-base no formato MM/AAAA. A nova tabela substitui a anterior da mesma fonte e tipo, fica gravada em `.runtime/reference_bases.sqlite3` e recalcula os orçamentos quando há códigos com unidade compatível. Esse arquivo local some quando o Streamlit Community Cloud recria o servidor; reenvie a tabela após um *Reboot app*.

Alterações nas premissas exigem clicar em **Atualizar orçamento**; até lá, o resultado anterior continua visível com um aviso. Marcar e desmarcar grupos e alterar o BDI fazem um recorte financeiro imediato do resultado existente. Projetos salvos na **Carteira de Projetos** (barra lateral) persistem no Supabase quando a seção `[storage]` está nos Secrets; detalhes em `docs/AUDITORIA.md`.

## Bases e premissas

- O banco `data/catalog.sqlite` contém 13.260 referências originais; `data/scope2_prices.json` acrescenta uma referência contratual da frota, totalizando 13.261 registros carregados.
- A via e o AMV nº 14 usam composições SIEC. A referência de material rodante vem do contrato CPTM 8186142011, data-base abril/2016, sem reajuste monetário. A extrapolação para via dupla SIEC é identificada nas regras.
- O número de AMVs informado é **total no corredor**, distribuído entre as linhas. Seu envelope é abatido da via corrida.
- A seleção de grupos não redimensiona geometria, duração, plataforma ou envelopes de AMV. Quantidades e valores são estimativas paramétricas, sujeitas a projeto e validação dos preços.
- As tabelas históricas do legado Parte 2 continuam no projeto para rastreabilidade e regressão interna, mas esse modelo não é oferecido na interface.
- Não havia bases SINAPI/SICRO nas planilhas recebidas. A hierarquia de fontes está no motor, sem inventar preços ou equivalências.
- O escopo preliminar de carga foi confrontado com as instruções [ISF-212 a ISF-218 do DNIT](https://www.gov.br/dnit/pt-br/ferrovias/instrucoes-e-procedimentos/instrucoes-de-servicos-ferroviarios), que separam lastro e sublastro, trilhos e dormentes, AMVs, pontes, sinalização e pátios para o projeto ferroviário.

## Estrutura

```text
app.py                         interface Streamlit e navegação
railbudget/engine.py           cenários, seleção, quantitativos e preços
railbudget/elevated.py         elevado: geometria, fundações, trechos e sensibilidade
railbudget/elevated_drawing.py desenho do elevado (corte e elevação em SVG)
railbudget/elevated_track.py   custo da via permanente no elevado e sensibilidade
railbudget/freight.py          ferrovia de carga e carga por eixo
railbudget/shortline.py        shortline: desvios, pátio e escopo pendente
railbudget/underground.py      subterrâneo preliminar
railbudget/vlt.py              VLT parametrizado pelo edital
railbudget/exporters.py        Excel, PDF e Word do orçamento
railbudget/comparison.py       comparação de dois cenários (A × B)
railbudget/localization.py     rótulos e memórias em português
railbudget/auth.py             login, perfis e permissões
railbudget/budget_store.py     carteira de projetos (Supabase ou SQLite)
railbudget/user_workspace.py   barra lateral "Seu espaço" e carteira
railbudget/reference_*.py      bases de referência enviadas pelo root
config/rules.json              composições e parâmetros
config/freight_axle.json       faixas e premissas da carga por eixo
config/coverage.json           cobertura da EAP de origem
data/catalog.sqlite           catálogo de preços
data/scope2_prices.json       referência contratual de material rodante
docs/MAPEAMENTO.md             decisões técnicas
docs/CHANGELOG.md              histórico de alterações e pontos de restauração
docs/AUDITORIA.md              segurança, persistência e Excel (23/10/2026)
tests/                         regressões de cálculo, interface e exportação
```

## Validação

Execute `python -m pytest -q` com as dependências de `requirements-dev.txt` (126 testes em 28/10/2026). As regressões mantêm a reprodução dos quatro totais históricos da Parte 2 para auditoria, além dos cenários SIEC, da interface e da geração de Excel, PDF e Word.

A aplicação pode ser executada localmente ou no Streamlit Community Cloud. Desde o PR #28 o Excel traz **valores fixos**, sem fórmulas: alterar um preço na planilha não recalcula o orçamento. Os identificadores internos do motor não são alterados pelos rótulos de apresentação.
