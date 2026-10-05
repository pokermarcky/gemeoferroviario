from railbudget.auth import UserContext, can


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

