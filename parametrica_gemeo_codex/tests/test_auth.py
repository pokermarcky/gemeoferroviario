import base64
from hashlib import pbkdf2_hmac

from railbudget.auth import (UserContext, _admin_accounts, _verify_password, is_primary_root,
    budget_download_limit, can, can_download_budget)
from pathlib import Path


def user(role):
    return UserContext(role, f"{role}@example.com", role, role, "test")


def test_permissoes_por_perfil():
    root = user("root")
    regular = user("user")
    demo = user("test")
    assert can(root, "manage_bases") and can(root, "download_excel")
    assert can(regular, "download_excel") and not can(regular, "manage_bases")
    assert can(demo, "calculate") and not can(demo, "save_budgets")
    assert not can(demo, "download_excel") and can(demo,"download_excel_trial")
    assert can_download_budget(demo,0) and not can_download_budget(demo,1)
    assert budget_download_limit(demo)==1 and budget_download_limit(root) is None
    assert not can(demo, "manage_bases")
    assert not can(user("unauthorized"), "calculate")


def test_recuperacao_e_email_root_nao_ficam_expostos_no_codigo_publico():
    source=(Path(__file__).resolve().parents[1]/"railbudget"/"auth.py").read_text(encoding="utf-8")
    assert "Recuperação administrativa" not in source
    assert "_recovery_login" not in source
    assert "pokermarcky90@gmail.com" not in source


def test_hash_administrativo_e_irreversivel_e_versionado():
    salt = b"sal-aleatorio-123"
    digest = pbkdf2_hmac("sha256", b"segredo-forte", salt, 600_000, dklen=32)
    encoded = "$".join((
        "pbkdf2_sha256",
        "600000",
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    ))
    assert _verify_password("segredo-forte", encoded)
    assert not _verify_password("senha-incorreta", encoded)
    assert not _verify_password("segredo-forte", encoded.replace("600000", "1000", 1))


def test_tres_contas_administrativas_sao_lidas_dos_secrets(monkeypatch):
    sections={
        "local_admin":{"username":"principal","password_hash":"h1"},
        "local_admin_secondary":{"username":"admin","password_hash":"h2"},
        "local_admin_backup":{"username":"contingencia","password_hash":"h3"},
    }
    monkeypatch.setattr("railbudget.auth._secrets_section",lambda name:sections.get(name,{}))
    assert _admin_accounts()==[("principal","h1"),("admin","h2"),("contingencia","h3")]


def test_somente_primeira_conta_e_root_principal(monkeypatch):
    monkeypatch.setattr("railbudget.auth._admin_accounts",lambda:[("principal@example.com","h1"),("admin","h2")])
    primary=UserContext("1","principal@example.com","Administrador","root","local")
    secondary=UserContext("2","admin","Administrador","root","local")
    assert is_primary_root(primary)
    assert not is_primary_root(secondary)


def test_tela_de_login_e_unica_sem_abas_por_perfil():
    source=(Path(__file__).resolve().parents[1]/"railbudget"/"auth.py").read_text(encoding="utf-8")
    assert 'with st.form("login_form"' in source
    assert 'st.tabs(["Administrador", "Conhecer o sistema"])' not in source
    assert 'form_submit_button("Entrar"' in source
