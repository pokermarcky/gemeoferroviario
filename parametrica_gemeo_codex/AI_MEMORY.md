# AI MEMORY — Parametric Rails

Última atualização: 28 de outubro de 2026.

## Identidade canônica

- Projeto: Parametric Rails / Gêmeo Ferroviário.
- GitHub oficial: `https://github.com/pokermarcky/gemeoferroviario`.
- Não tratar `railparametric` como nome atual do repositório.
- Branch padrão: `main`.
- Aplicação: `parametrica_gemeo_codex/app.py`.
- Diretório de execução: `parametrica_gemeo_codex`.

## Estado consolidado

- `gemeoferroviario` é o único repositório do projeto que deve permanecer em uso.
- `gemeodigital_ferrovia`, `renda-fixa-br` e `cadastro` foram excluídos com autorização explícita do proprietário.
- Não recriar, importar ou vincular automaticamente os três repositórios removidos.
- O repositório principal não foi renomeado, para preservar as coordenadas da implantação existente no Streamlit Community Cloud.
- A validação de encerramento registrou 75 testes aprovados; em 28/10/2026 a suíte tem 113.
- Aplicação publicada: `https://railparametric.streamlit.app/`.
- Histórico de alterações: `docs/CHANGELOG.md` (uma entrada por PR).
- Pontos de restauração (branches, pois tags não são publicadas pelas sessões automatizadas): `backup/estavel-2026-10-23` e `backup/pre-melhorias-2026-10-28`.
- Nunca definir `RAILPARAMETRIC_TEST_MODE` no Streamlit Cloud: essa variável dispensa o login e entra como root.

## Streamlit Community Cloud

Usar estas coordenadas ao conferir ou refazer a implantação:

```text
owner: pokermarcky
repository: gemeoferroviario
branch: main
entrypoint: parametrica_gemeo_codex/app.py
```

O Community Cloud identifica a aplicação por proprietário, repositório, branch e caminho do arquivo principal. Antes de alterar qualquer uma dessas coordenadas:

1. registrar configurações e secrets;
2. excluir de forma controlada a implantação atual;
3. realizar a mudança no GitHub;
4. implantar novamente;
5. restaurar secrets e executar uma verificação funcional.

Nunca registrar valores reais de secrets neste arquivo ou no repositório.

## Validação mínima para futuras alterações

Executar a partir de `parametrica_gemeo_codex`:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Também confirmar:

- acesso ao repositório oficial;
- branch padrão `main`;
- existência de `app.py`, `requirements.txt` e `.streamlit/config.toml`;
- carregamento da URL publicada no Streamlit, quando a URL estiver disponível;
- ausência de secrets ou credenciais no Git.

## Regras de continuidade

- Preservar código, histórico e configuração do repositório oficial.
- Não afirmar que uma implantação está saudável apenas porque o repositório está acessível; testar a URL publicada separadamente.
- Não alterar nome do repositório, branch, entrypoint ou secrets sem autorização explícita.
- Registrar mudanças operacionais relevantes em `docs/` e atualizar este arquivo quando o estado canônico mudar.
- O estado de encerramento desta limpeza está documentado em `docs/ENCERRAMENTO_REPOSITORIOS.md`.
