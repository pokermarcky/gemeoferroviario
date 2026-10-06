import base64
from hashlib import pbkdf2_hmac

from railbudget.auth import UserContext, _verify_password, budget_download_limit, can, can_download_budget
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
