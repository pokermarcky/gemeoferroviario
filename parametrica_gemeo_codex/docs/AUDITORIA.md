# Auditoria de segurança, persistência, elevado e Excel — 23/10/2026

Ponto de restauração anterior: branch `backup/estavel-2026-10-23` (commit `08fdea8`).
Escopo: pendências P0/P1 do dossiê técnico. Nenhuma regra de cálculo, preço ou dado foi alterado.

## Resumo

| Verificação | Resultado |
|---|---|
| Secrets no repositório e no histórico | Nenhum valor real encontrado |
| Persistência da carteira (salvar, sair/entrar, reiniciar) | Correta no código; 6 testes novos com Supabase simulado e SQLite |
| Elevado de passageiros com cálculo independente | 51 itens e totais reconciliam com o motor; 3 testes novos |
| Excel exportado | Abre sem erro no LibreOffice, 0 células com erro, totais fecham; 6 testes novos |

Testes: 85 antes, 100 depois (`python -m pytest -q` em `parametrica_gemeo_codex`).

## 1. Secrets e credenciais

Método: busca por padrões de chaves (JWT/Supabase, `sb_secret_`, tokens GitHub, OpenAI, AWS, Google, chaves privadas), hashes PBKDF2 reais, URLs `*.supabase.co` e atribuições de senha em todos os 229 commits de todos os branches, e lista de arquivos já adicionados ao histórico.

- Nunca houve `secrets.toml`, `.env` ou arquivo de chaves no histórico. `.gitignore` exclui `.streamlit/secrets.toml` e `.runtime/`.
- `secrets.example.toml` contém apenas marcadores (`EMAIL_DO_ADMINISTRADOR`, `SALT_BASE64`, `SERVICE_ROLE_KEY`, `SEU_PROJETO`), inclusive nas versões antigas (Google OAuth e senha em texto).
- O código lê credenciais somente de `st.secrets` (`[local_admin*]`, `[storage]`) e de variáveis de ambiente (`RAILPARAMETRIC_TEST_MODE`, `RAILPARAMETRIC_BUDGET_DB`). A chave do Supabase vai somente no cabeçalho da requisição feita pelo servidor e não aparece em mensagens de erro (teste `test_falha_do_supabase_nao_expoe_a_chave`).
- Senhas administrativas: PBKDF2-SHA256 com 600.000 iterações, salt ≥ 16 bytes e comparação em tempo constante.

Pontos de atenção (recomendações, sem alteração):

1. **`RAILPARAMETRIC_TEST_MODE=1` dispensa o login e entra como root.** Nunca definir essa variável no Streamlit Cloud. Melhoria sugerida: aceitar o modo de teste só quando também não houver `[local_admin]` nos Secrets.
2. O bloqueio após 5 tentativas vale por sessão do navegador; abrir nova sessão recomeça a contagem. O custo do PBKDF2 limita a força bruta, mas um limite por login guardado no servidor seria mais robusto.
3. O acesso de demonstração (`teste` / senha pública no código) é intencional e sem privilégios; o limite de 1 Excel também é por sessão.
4. A chave `service_role` ignora o RLS do Supabase. O código filtra sempre por `owner_id` (teste `test_supabase_filtra_sempre_pelo_proprietario`). Recomenda-se ativar RLS na tabela `saved_budgets` sem políticas públicas, para que a chave `anon` não leia nada.

## 2. Persistência da carteira

Leitura de `railbudget/budget_store.py` e `railbudget/auth.py`:

- O dono do orçamento é `sha256(login)[:24]`, estável entre logins; sair e entrar recupera a mesma carteira.
- Com `[storage]` configurado, os dados ficam no Supabase e sobrevivem a reinicializações. Sem ele, ficam em SQLite em `.runtime/`, que **o Streamlit Cloud apaga ao recriar o servidor**. Conferir no painel do Streamlit se a seção `[storage]` está preenchida (não é possível verificar daqui).
- Somente o root principal (primeira conta de `[local_admin]`) salva, edita e exclui. Trocar esse login muda o identificador e a carteira antiga deixa de aparecer (os dados continuam no banco).

Testes novos em `tests/test_persistencia.py` (Supabase simulado por um PostgREST em memória, sem rede):
salvar → sair → entrar; salvar → editar → reiniciar (sessão limpa e módulo recarregado) → listar → excluir; isolamento por dono; erro do Supabase sem vazar a chave; mesmo ciclo em SQLite; perfil de teste sem gravação.

Pendente para o Marcelo: um teste manual no site publicado (salvar um projeto, sair, entrar, e conferir de novo após um *Reboot app* no painel).

## 3. Elevado de passageiros com cálculo independente

`tests/test_elevado_independente.py` usa um cenário fora do padrão (2,5 km, via dupla, 2 AMVs, altura 12 m, vão 30 m, tabuleiro 12 m, hélice contínua Ø 0,60 m, 25 m, 6 estacas/apoio, geotecnia desfavorável). Recalcula as quantidades direto das fórmulas de `config/rules.json`, com avaliador e leitura de preços próprios, e compara item a item com o motor.

- 51 itens do elevado: quantidades, códigos, preços unitários e totais iguais ao motor.
- Conferência manual: 84 vãos, 85 apoios, estacas 85 × 6 × 25 × 1,5 × 1,25 = 23.906,25 m, sondagens 85 × 20 × 1,25 m, área do tabuleiro 30.200 m².
- Direto, BDI, total e R$/km fecham com arredondamento em centavos.

Observação (recomendação): a aba **Elevado** do Excel e o resumo mostram "Extensão total de estacas" = apoios × estacas × profundidade (12.750 m no cenário acima), enquanto o orçamento cobra 23.906,25 m, porque inclui o fator de fundação da via dupla (1,5) e o coeficiente geotécnico (1,25). O valor orçado está coerente com as regras; o indicador é geométrico. Sugere-se explicitar isso no rótulo ou exibir os dois números.

## 4. Excel exportado

Gerado para superfície padrão e para o elevado acima; aberto e recalculado no LibreOffice 24.2 por automação (UNO).

- 14 a 15 abas (Resumo, EAP, Premissas, Elevado, Mercado/Provisão quando aplicável, SIEC_SERVICOS e uma por grupo). 0 células com erro.
- Soma da coluna "Custo total" da EAP = custo direto do motor; Resumo com direto, total e grupos iguais ao motor.
- **O arquivo não contém fórmulas** desde o PR #28 ("Excel nativo sem pós-processamento"): todos os valores são fixos. Por isso `docs/VALIDACAO.md` (13/09/2026, "alterar um preço modificou o orçamento") e `docs/PLANO_APRIMORAMENTOS.md` ("Excel com PROCV") estão desatualizados nesse ponto.
- Corrigido: a aba EAP dizia "preços vinculados por PROCV exato" e as abas de grupo "valores vinculados à EAP". Os textos agora dizem que os valores são copiados (fixos, sem fórmulas).
- Uma linha da EAP difere de quantidade × preço em R$ 0,01 por arredondamento de ponto flutuante; o total do item segue a regra do motor.
- Não foi possível abrir no Microsoft Excel real neste ambiente; continua pendente (P1).

Decisão para o Marcelo: manter o Excel com valores fixos (mais estável, sem reparo ao abrir) ou voltar a ter fórmulas vivas de preço × quantidade.

## Outras correções pequenas

- Removidos do Git 4 arquivos `.pyc` de `railbudget/__pycache__/` que estavam versionados apesar do `.gitignore`.

## Como reproduzir

```bash
cd parametrica_gemeo_codex
python -m pip install -r requirements-dev.txt
python -m pytest -q tests/test_persistencia.py tests/test_elevado_independente.py tests/test_excel_integridade.py
```
