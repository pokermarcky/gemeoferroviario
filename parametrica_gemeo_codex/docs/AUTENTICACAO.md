# Autenticação e Meus Orçamentos

## Perfis

- **root**: o e-mail `pokermarcky90@gmail.com`, os e-mails de contingência e o acesso emergencial. Pode usar todas as funções.
- **user**: qualquer conta autenticada pelo Google. Pode calcular, gerar Excel e salvar seus orçamentos, mas não pode substituir bases ou enviar planilhas.
- **test**: login local `teste`. Pode conhecer, calcular e salvar temporariamente, mas não pode alterar bases nem gerar Excel.

As restrições são verificadas no código antes de criar uploads ou downloads. Não dependem apenas da aparência da tela.

## Plano B do administrador

Há duas camadas independentes:

1. `backup_root_emails`: permite cadastrar uma segunda conta Google como root.
2. `emergency_password_hash`: habilita o usuário local `root` com uma chave de recuperação, mesmo sem acesso ao Google.

Crie uma chave longa, exclusiva, guarde-a em um gerenciador de senhas e grave somente o SHA-256 nos Secrets:

```python
from hashlib import sha256
print(sha256("SUA-CHAVE-FORTE".encode()).hexdigest())
```

Nunca publique `.streamlit/secrets.toml` no GitHub. Copie `secrets.example.toml` somente para a área **Secrets** do Streamlit Community Cloud e substitua os marcadores.

## Google OIDC

No Google Cloud, crie um cliente OAuth do tipo aplicação Web e cadastre exatamente:

```text
https://railparametric.streamlit.app/oauth2callback
```

O código usa `st.login("google")`, `st.user` e `st.logout()`.

## Base persistente de orçamentos

Crie no Supabase a tabela abaixo. A chave `service_role` fica apenas no servidor Streamlit e jamais deve ser enviada ao navegador ou adicionada ao repositório.

```sql
create table if not exists public.saved_budgets (
  id uuid primary key,
  owner_id text not null,
  owner_email text not null,
  name text not null check (char_length(name) between 1 and 80),
  modality text not null,
  total numeric not null,
  result_json jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists saved_budgets_owner_created
  on public.saved_budgets (owner_id, created_at desc);
```

Sem a seção `[storage]`, a aplicação usa armazenamento temporário por sessão e informa essa condição na barra lateral.

