from railbudget.auth import UserContext, can
from pathlib import Path


def user(role):
    return UserContext(role, f"{role}@example.com", role, role, "test")


def test_permissoes_por_perfil():
    root = user("root")
    regular = user("user")
    demo = user("test")
    assert can(root, "manage_bases") and can(root, "download_excel")
    assert can(regular, "download_excel") and not can(regular, "manage_bases")
    assert can(demo, "calculate") and can(demo, "save_budgets")
    assert not can(demo, "download_excel") and not can(demo, "manage_bases")
    assert not can(user("unauthorized"), "calculate")


def test_recuperacao_e_email_root_nao_ficam_expostos_no_codigo_publico():
    source=(Path(__file__).resolve().parents[1]/"railbudget"/"auth.py").read_text(encoding="utf-8")
    assert "Recuperação administrativa" not in source
    assert "_recovery_login" not in source
    assert "pokermarcky90@gmail.com" not in source
