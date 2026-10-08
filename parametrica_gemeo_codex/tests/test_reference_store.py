from railbudget.auth import UserContext
from railbudget.reference_data import ReferenceBase
from railbudget.reference_store import load_reference_bases, save_reference_base


def base(period,price):
    return ReferenceBase("SIEC","Serviços",period,"siec.xlsx",period,
        [{"code":"1","description":"Serviço","unit":"m","price":price,"date":period}],
        ["Código","Preço"],["Serviços"])


def test_ultima_base_substitui_anterior_e_sobrevive_a_nova_sessao(monkeypatch,tmp_path):
    monkeypatch.setenv("RAILPARAMETRIC_REFERENCE_DB",str(tmp_path/"references.sqlite3"))
    root=UserContext("root","root@example.com","Administrador","root","test")
    save_reference_base(root,base("07/2026",10))
    save_reference_base(root,base("08/2026",12))
    loaded=load_reference_bases()
    assert len(loaded)==1
    assert loaded[("SIEC","Serviços")].period=="08/2026"
    assert loaded[("SIEC","Serviços")].records[0]["price"]==12


def test_usuario_sem_permissao_nao_substitui_base(monkeypatch,tmp_path):
    monkeypatch.setenv("RAILPARAMETRIC_REFERENCE_DB",str(tmp_path/"references.sqlite3"))
    visitor=UserContext("demo","teste@local","Visitante","test","local")
    try:
        save_reference_base(visitor,base("08/2026",12))
    except PermissionError:
        pass
    else:
        raise AssertionError("Upload não autorizado foi aceito")
