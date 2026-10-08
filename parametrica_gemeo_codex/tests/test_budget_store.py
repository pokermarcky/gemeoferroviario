from railbudget.auth import UserContext
from railbudget.budget_store import ensure_budget, list_budgets, save_budget, storage_mode


def test_sqlite_preserva_orcamento_por_usuario(monkeypatch,tmp_path):
    monkeypatch.setenv("RAILPARAMETRIC_BUDGET_DB",str(tmp_path/"budgets.sqlite3"))
    root=UserContext("root-1","root@example.com","Administrador","root","test-suite")
    other=UserContext("user-2","user@example.com","Usuário","user","test")
    result={"total":1234.56,"scenario":{"km":1},"items":[]}
    save_budget(root,"Linha teste","Ferrovia de passageiro",result)
    assert storage_mode(root)=="sqlite"
    saved=list_budgets(root.user_id,root)
    assert len(saved)==1
    assert saved[0]["name"]=="Linha teste"
    assert saved[0]["result_json"]==result
    assert list_budgets(other.user_id,other)==[]


def test_acesso_compartilhado_permanece_isolado_na_sessao():
    demo=UserContext("demo-teste","teste@railparametric.local","Visitante","test","local")
    assert storage_mode(demo)=="session"


def test_apenas_root_principal_pode_salvar_orcamento(monkeypatch,tmp_path):
    monkeypatch.setenv("RAILPARAMETRIC_BUDGET_DB",str(tmp_path/"budgets.sqlite3"))
    demo=UserContext("demo-teste","teste@railparametric.local","Visitante","test","local")
    try:
        save_budget(demo,"Não autorizado","Ferrovia de passageiro",{"total":1})
    except PermissionError:
        pass
    else:
        raise AssertionError("Orçamento de usuário não autorizado foi salvo")


def test_projeto_inicial_e_criado_sem_duplicacao(monkeypatch,tmp_path):
    monkeypatch.setenv("RAILPARAMETRIC_BUDGET_DB",str(tmp_path/"budgets.sqlite3"))
    root=UserContext("root","root@example.com","Administrador","root","test-suite")
    result={"total":191008605.92,"per_km":73464848.43}
    ensure_budget(root,"VLT Aeroporto - Castelão","VLT",result)
    ensure_budget(root,"VLT Aeroporto - Castelão","VLT",result)
    saved=list_budgets(root.user_id,root)
    assert len(saved)==1
    assert saved[0]['modality']=='VLT'
