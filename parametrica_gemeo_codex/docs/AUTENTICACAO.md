# Autenticação e Meus Orçamentos

## Perfis

- **root**: os e-mails cadastrados em `root_emails`. Pode usar todas as funções.
- **user**: somente contas Google presentes na allowlist de e-mails ou domínios. Pode calcular, gerar Excel e salvar seus orçamentos, mas não pode substituir bases ou enviar planilhas.
- **test**: login local `teste`. Pode conhecer, calcular e salvar temporariamente, mas não pode alterar bases nem gerar Excel.

As restrições são verificadas no código antes de criar uploads ou downloads. Não dependem apenas da aparência da tela.

## Plano B do administrador

O plano B fica fora da interface pública e possui duas camadas:

1. cadastrar previamente uma segunda conta Google em `root_emails`;
2. se ambas as contas forem perdidas, o proprietário altera `root_emails` diretamente nos Secrets do Streamlit Cloud usando o acesso de proprietário da implantação.

Não existe formulário, rota ou senha de recuperação administrativa dentro do site público.

Nunca publique `.streamlit/secrets.toml` no GitHub. Copie `secrets.example.toml` somente para a área **Secrets** do Streamlit Community Cloud e substitua os marcadores.

## Google OIDC

No Google Cloud, crie um cliente OAuth do tipo aplicação Web e cadastre exatamente:

```text
https://railparametric.streamlit.app/oauth2callback
```

O código usa `st.login("google")`, `st.user` e `st.logout()`.

Por padrão, `allow_all_google_users = false`. Novos usuários devem ser incluídos explicitamente em `allowed_emails` ou em um domínio confiável de `allowed_domains`.

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
