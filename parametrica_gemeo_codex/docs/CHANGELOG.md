# Histórico de mudanças

Registro das mudanças que chegam à `main`, da mais recente para a mais antiga. Para voltar a um estado anterior, veja `docs/RESTAURACAO.md`.

## Como acrescentar uma entrada

Toda mudança mesclada na `main` (por pessoa, Codex ou Claude) acrescenta uma linha **no topo** da seção do dia, no mesmo PR da mudança:

```markdown
- #NN — Título curto do PR. O que mudou para o usuário, em uma frase. Arquivos principais. Testes: N aprovados.
```

Regras:

- Diga se o PR mexe em cálculo (`railbudget/engine.py`, `expressions.py`), dados (`data/`) ou regras (`config/rules.json`). Essas mudanças exigem um ponto de restauração novo antes do merge.
- Ao reverter um PR, registre a reversão e cite o PR desfeito.
- Ao criar um ponto de restauração `backup/...`, registre-o aqui e na tabela de `docs/RESTAURACAO.md`.
- PRs ainda abertos ficam em "Em andamento" e passam para a data do merge quando forem mesclados.

## Em andamento

- #44 — Memórias de cálculo integralmente em português (etapa 3 do plano). Branch `nomenclatura-portugues`, aguardando revisão. Tradução só de exibição (`railbudget/localization.py`); expressões, chaves de `rules.json` e dados salvos não mudam.

## 2026-10-23

- Documentação de restauração e este histórico (`docs/RESTAURACAO.md`, `docs/CHANGELOG.md`). Remoção de `__pycache__` versionados por engano, `.gitignore` ampliado e correção de "seis grupos" para "nove grupos" em `PLANO_APRIMORAMENTOS.md`. Sem mudança de cálculo, dados ou regras.
- Ponto de restauração `backup/estavel-2026-10-23` criado no commit `08fdea8` (após o #50).
- #50 — Cartão "Seu espaço" na paleta vermelho e amarelo. Só interface (CSS em `railbudget/interface.py`).
- #47 — Tema vermelho e amarelo em degradê (`#b8322a → #e2712a → #f4b63f`), substituindo o verde sálvia do #48 e mantendo a fonte do #49. Só interface.
- #49 — Corrige a configuração do tema Streamlit (`.streamlit/config.toml`). Só interface.
- #48 — Interface em verde sálvia claro. Substituída pelo #47 no mesmo dia.
- #46 — Volta a cor original do fundo da página (reverte o #45).
- #45 — Fundo da página em tom alaranjado. Revertido pelo #46.
- Memória operacional do projeto (`AI_MEMORY.md`) e documentação do encerramento dos repositórios antigos (`docs/ENCERRAMENTO_REPOSITORIOS.md`).

## Antes de 2026-10-23

O histórico anterior (PRs #25 a #43: autenticação, Carteira de Projetos, Excel nativo, VLT Aeroporto–Castelão, via subterrânea preliminar, elevado de passageiros paramétrico) está no `git log` da `main` e nas páginas dos PRs no GitHub.
