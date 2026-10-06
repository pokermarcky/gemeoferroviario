# Autenticação e Meus Orçamentos

## Perfis

- **root**: conta local cadastrada exclusivamente em `[local_admin]` nos Secrets. Pode usar todas as funções.
- **administrador secundário**: conta cadastrada em `[local_admin_secondary]`, com os mesmos poderes completos do root.
- **root de contingência**: segunda conta independente em `[local_admin_backup]`.
- **test**: login local `teste`. Pode conhecer, calcular, salvar temporariamente e baixar um único orçamento em Excel por sessão. Não pode alterar bases.

As restrições são verificadas no código antes de criar uploads ou downloads. Não dependem apenas da aparência da tela.

## Plano B do administrador

O plano B fica fora da interface pública e possui duas camadas:

1. cadastrar previamente uma segunda conta local em `[local_admin_backup]`, com e-mail e senha diferentes;
2. se ambas as contas forem perdidas, o proprietário altera as credenciais diretamente nos Secrets do Streamlit Cloud usando o acesso de proprietário da implantação.

Não existe formulário, rota ou senha de recuperação administrativa dentro do site público.

Nunca publique `.streamlit/secrets.toml` no GitHub. Copie `secrets.example.toml` somente para a área **Secrets** do Streamlit Community Cloud e substitua os marcadores. O campo `password_hash` recebe somente o hash PBKDF2-SHA256 com salt aleatório; a senha em texto puro não é armazenada nem no repositório nem nos Secrets.

## Autenticação local

O site não utiliza Google Cloud. O usuário e o hash irreversível da senha privilegiada são lidos somente dos Secrets privados do Streamlit. Após cinco tentativas inválidas na mesma sessão, o acesso administrativo é bloqueado por quinze minutos. A sessão root expira após oito horas e a sessão de demonstração após uma hora.

A interface não contém recuperação administrativa. A contingência é operacional, pelo segundo administrador e pelo painel privado da implantação.

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

Sem a seção `[storage]`, root e futuros usuários individuais usam uma base SQLite local protegida, suficiente para preservar os orçamentos entre logout e login no mesmo servidor. Como o Streamlit Community Cloud pode recriar o servidor em reinicializações ou novas implantações, a seção `[storage]` com Supabase continua sendo a opção recomendada para persistência definitiva. O login compartilhado de demonstração permanece isolado por sessão para não expor os orçamentos de um visitante a outro.
