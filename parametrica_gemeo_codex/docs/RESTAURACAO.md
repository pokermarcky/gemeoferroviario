# Restauração — como voltar a um ponto estável

Última atualização: 23 de outubro de 2026.

Este documento explica como devolver o Parametric Rails a um estado conhecido e funcional caso uma alteração cause problema ("crise"). Leia também `AI_MEMORY.md` (coordenadas canônicas) e `docs/CHANGELOG.md` (o que mudou em cada PR).

## Pontos de restauração disponíveis

| Ponto | Tipo | Commit | Estado |
| --- | --- | --- | --- |
| `backup/estavel-2026-10-23` | branch no GitHub | `08fdea8` | `main` após o PR #50 (tema vermelho e amarelo, cartão "Seu espaço"), 75 testes aprovados. Anterior aos PRs #44, #52, #53 e #54. |

Regras para pontos de restauração:

- Um branch `backup/...` **nunca** recebe commits novos. Ele só aponta para um estado aprovado da `main`.
- Antes de uma série grande de mudanças, crie um novo ponto com a data do dia e acrescente uma linha na tabela acima:

  ```bash
  git fetch origin main
  git push origin origin/main:refs/heads/backup/estavel-AAAA-MM-DD
  ```

- Se preferir também uma tag anotada (útil para a página Releases do GitHub), crie-a localmente com acesso de proprietário:

  ```bash
  git tag -a estavel-2026-10-23 08fdea8 -m "Ponto estável da main em 23/10/2026"
  git push origin estavel-2026-10-23
  ```

  Observação: as sessões do Claude não conseguem publicar tags neste repositório (o proxy bloqueia), por isso os pontos de restauração são branches `backup/...`.

## Como voltar

Escolha a opção menos destrutiva que resolva o problema.

### 1. Desfazer um único PR (recomendado)

Pelo GitHub: abra o PR mesclado e clique em **Revert**. Isso cria um novo PR que desfaz exatamente aquela mudança, preservando o histórico. Foi assim que o PR #45 (fundo laranja) foi desfeito pelo PR #46.

Pela linha de comando:

```bash
git fetch origin main
git checkout -b reverte-pr-NN origin/main
git revert -m 1 <sha-do-merge-do-PR>   # use -m 1 só se for commit de merge
git push -u origin reverte-pr-NN       # depois abra o PR e mescle
```

### 2. Voltar a `main` inteira para um ponto de restauração, sem apagar histórico

Cria um commit novo cujo conteúdo é idêntico ao ponto escolhido:

```bash
git fetch origin main backup/estavel-2026-10-23
git checkout -b restaura-estavel origin/main
git checkout origin/backup/estavel-2026-10-23 -- .
git commit -m "Restaura o estado de backup/estavel-2026-10-23"
git push -u origin restaura-estavel    # abra o PR, rode os testes e mescle
```

### 3. Reset forçado (último recurso)

Apaga da `main` tudo o que veio depois do ponto. Só com autorização explícita do proprietário e depois de criar um branch `backup/...` do estado atual, para nada se perder:

```bash
git push origin origin/main:refs/heads/backup/antes-do-reset-AAAA-MM-DD
git push --force-with-lease origin origin/backup/estavel-2026-10-23:main
```

## Depois de restaurar

1. Rode os testes em `parametrica_gemeo_codex`:

   ```bash
   python -m pip install -r requirements-dev.txt
   python -m pytest -q
   ```

2. O Streamlit Community Cloud reimplanta sozinho quando a `main` muda. Abra https://railparametric.streamlit.app/ e confira login, cálculo de um cenário e download do Excel.
3. Se a aplicação não voltar, em **Manage app** use **Reboot app**. Se for preciso refazer a implantação, use exatamente as coordenadas de `AI_MEMORY.md` (owner `pokermarcky`, repositório `gemeoferroviario`, branch `main`, entrypoint `parametrica_gemeo_codex/app.py`) e recoloque os secrets a partir da cópia guardada pelo proprietário. Nunca registre valores de secrets no repositório.
4. Registre a restauração em `docs/CHANGELOG.md`.

## Onde estão os dados essenciais

| Item | Local | Observação |
| --- | --- | --- |
| Catálogo de preços e proveniência | `parametrica_gemeo_codex/data/catalog.sqlite` | Versionado no Git; volta junto com o commit restaurado. Gerado por `railbudget/importer.py`. |
| Regras de composição, geometria e os nove grupos | `parametrica_gemeo_codex/config/rules.json` | Versionado; gerado por `railbudget/build_rules.py` a partir do catálogo. |
| Cobertura das EAPs de origem | `parametrica_gemeo_codex/config/coverage.json` | Versionado. |
| Snapshots, inventário e preços do escopo 2 | `parametrica_gemeo_codex/data/*.json` | Versionados. |
| Projetos e orçamentos salvos pelos usuários | Supabase (`railbudget/budget_store.py`) ou `parametrica_gemeo_codex/.runtime/` em modo local | **Não** estão no Git; restaurar o código não apaga nem recupera esses dados. |
| Secrets (Supabase, administradores) | Painel do Streamlit Cloud / `.streamlit/secrets.toml` local | Fora do Git (`.gitignore`). Guardar cópia segura fora do repositório. |
| Tema visual | CSS `STYLE` em `railbudget/interface.py` e `[theme]` em `.streamlit/config.toml` | Versionados. |

Se um problema afetar o cálculo, confira primeiro se `catalog.sqlite` e `rules.json` do commit atual são os mesmos do ponto estável:

```bash
git diff --stat origin/backup/estavel-2026-10-23 origin/main -- parametrica_gemeo_codex/data parametrica_gemeo_codex/config
```
