# Encerramento da organização dos repositórios

Data da verificação: 23 de outubro de 2026.

## Estado final

O projeto oficial permanece no GitHub em:

- Repositório: `pokermarcky/gemeoferroviario`
- Branch principal: `main`
- Aplicação Streamlit: `parametrica_gemeo_codex/app.py`
- Commit verificado antes desta documentação: `71a474af071ea045c13888a57231f28466849f31`
- Descrição: `Gêmeos digitais de obras ferroviárias`

O repositório não foi renomeado para evitar a perda de administração da implantação atual no Streamlit Community Cloud. Código, histórico e configuração do projeto principal foram preservados.

## Repositórios removidos

Os seguintes repositórios foram excluídos da conta `pokermarcky`, conforme autorização do proprietário:

- `gemeodigital_ferrovia`
- `renda-fixa-br`
- `cadastro`

A verificação final da API do GitHub retornou `404 Not Found` para os três endereços, e a listagem da conta retornou apenas `pokermarcky/gemeoferroviario`.

## Verificações realizadas

- O repositório principal continua público, ativo e acessível.
- A branch padrão continua sendo `main`.
- O arquivo de entrada do Streamlit permanece em `parametrica_gemeo_codex/app.py`.
- A configuração do Streamlit permanece em `parametrica_gemeo_codex/.streamlit/config.toml`.
- A árvore do projeto e o commit principal foram consultados após a exclusão dos demais repositórios.
- A suíte automatizada foi executada a partir de uma cópia limpa do repositório.
- Resultado: **75 testes aprovados**.

## Ligação com o Streamlit

| Campo | Valor |
|---|---|
| Proprietário | `pokermarcky` |
| Repositório | `gemeoferroviario` |
| Branch | `main` |
| Arquivo principal | `parametrica_gemeo_codex/app.py` |

Não renomear o repositório, a branch ou o arquivo principal sem antes excluir de forma controlada a implantação no Streamlit, realizar a mudança e implantar novamente. Os secrets do Streamlit não fazem parte do Git e devem ser preservados separadamente.

## Recuperação

Caso uma exclusão tenha sido acidental, a recuperação depende da janela e das condições oferecidas pelo GitHub em **Settings → Repositories → Deleted repositories**. Nenhuma restauração foi necessária durante esta atividade.
