"""Persistência da carteira: salvar, sair/entrar e reiniciar o servidor.

O Supabase é simulado por um servidor PostgREST em memória; nenhum acesso de
rede é feito e nenhum secret real é usado.
"""
import base64
from hashlib import pbkdf2_hmac
import importlib
import io
import json
from urllib.error import HTTPError
from urllib.parse import parse_qs, unquote, urlsplit

import pytest
import streamlit as st

from railbudget import auth, budget_store


FAKE_URL = "https://projeto-ficticio.supabase.co"
FAKE_KEY = "chave-ficticia-de-teste"
ADMIN_LOGIN = "admin@test.invalid"


def _hash(password):
    salt = b"sal-de-teste-0123456789"
    digest = pbkdf2_hmac("sha256", password.encode(), salt, 600_000, dklen=32)
    return "$".join(("pbkdf2_sha256", "600000",
        base64.b64encode(salt).decode(), base64.b64encode(digest).decode()))


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class FakePostgrest:
    """Imita o subconjunto do PostgREST usado por ``budget_store``."""

    def __init__(self):
        self.rows = []
        self.requests = []

    def __call__(self, request, timeout=None):
        self.requests.append(request)
        assert request.get_header("Apikey") == FAKE_KEY
        assert request.get_header("Authorization") == "Bearer " + FAKE_KEY
        parts = urlsplit(request.full_url)
        assert parts.path == "/rest/v1/saved_budgets"
        filters = {key: unquote(values[0]).removeprefix("eq.")
            for key, values in parse_qs(parts.query).items() if key in ("id", "owner_id")}
        matches = [row for row in self.rows if all(str(row[k]) == v for k, v in filters.items())]
        method = request.get_method()
        if method == "GET":
            body = sorted(matches, key=lambda row: row["created_at"], reverse=True)
        elif method == "POST":
            row = json.loads(request.data.decode())
            self.rows.append(row)
            body = [row]
        elif method == "PATCH":
            for row in matches:
                row.update(json.loads(request.data.decode()))
            body = matches
        elif method == "DELETE":
            self.rows = [row for row in self.rows if row not in matches]
            body = matches
        else:
            raise AssertionError(method)
        return FakeResponse(json.dumps(body).encode())


@pytest.fixture
def admin_secrets(monkeypatch):
    sections = {"local_admin": {"username": ADMIN_LOGIN, "password_hash": _hash("senha-de-teste")}}
    monkeypatch.setattr(auth, "_secrets_section", lambda name: sections.get(name, {}))
    st.session_state.clear()
    yield
    st.session_state.clear()


@pytest.fixture
def supabase(monkeypatch):
    server = FakePostgrest()
    config = {"url": FAKE_URL, "key": FAKE_KEY, "table": "saved_budgets"}
    monkeypatch.setattr(budget_store, "_storage_config", lambda: dict(config))
    monkeypatch.setattr(budget_store, "urlopen", server)
    return server


def _login():
    """Reproduz o estado de sessão gravado por ``auth._login`` após senha válida."""
    st.session_state.local_auth = {"role": "root", "username": ADMIN_LOGIN, "issued_at": __import__("time").time()}
    user = auth._local_user()
    assert user is not None and user.role == "root"
    return user


def _logout():
    st.session_state.pop("local_auth", None)
    st.session_state.pop("results", None)
    st.session_state.pop("display_results", None)
    assert auth._local_user() is None


RESULT = {"total": 1234567.89, "per_km": 1234567.89, "scenario": {"km": 1.0, "configuration": "Elevado"}}


def test_supabase_preserva_carteira_apos_sair_e_entrar(admin_secrets, supabase):
    user = _login()
    assert budget_store.storage_mode(user) == "supabase"
    saved = budget_store.save_budget(user, "  Linha Norte  ", "Ferrovia de passageiro", RESULT)
    assert saved["name"] == "Linha Norte"

    _logout()
    again = _login()
    assert again.user_id == user.user_id
    rows = budget_store.list_budgets(again.user_id, again)
    assert [row["name"] for row in rows] == ["Linha Norte"]
    assert rows[0]["result_json"] == RESULT
    assert rows[0]["total"] == RESULT["total"]


def test_supabase_preserva_carteira_apos_reiniciar_servidor(admin_secrets, supabase, monkeypatch):
    user = _login()
    budget_store.save_budget(user, "Linha Sul", "VLT", RESULT)
    budget_store.update_budget(user, budget_store.list_budgets(user.user_id, user)[0]["id"], "Linha Sul revisada")

    # Reinício: a sessão e o módulo são recriados; só o banco remoto sobrevive.
    st.session_state.clear()
    reloaded = importlib.reload(budget_store)
    monkeypatch.setattr(reloaded, "_storage_config",
        lambda: {"url": FAKE_URL, "key": FAKE_KEY, "table": "saved_budgets"})
    monkeypatch.setattr(reloaded, "urlopen", supabase)
    user = _login()
    rows = reloaded.list_budgets(user.user_id, user)
    assert [row["name"] for row in rows] == ["Linha Sul revisada"]

    reloaded.delete_budget(user, rows[0]["id"])
    assert reloaded.list_budgets(user.user_id, user) == []
    assert all(request.get_method() in {"GET", "POST", "PATCH", "DELETE"} for request in supabase.requests)


def test_supabase_filtra_sempre_pelo_proprietario(admin_secrets, supabase):
    user = _login()
    saved = budget_store.save_budget(user, "Minha linha", "VLT", RESULT)
    supabase.rows.append({**saved, "id": "alheio", "owner_id": "outro-dono", "name": "Linha alheia"})
    assert [row["name"] for row in budget_store.list_budgets(user.user_id, user)] == ["Minha linha"]
    with pytest.raises(LookupError):
        budget_store.delete_budget(user, "alheio")
    with pytest.raises(LookupError):
        budget_store.update_budget(user, "alheio", "Invasão")
    assert any(row["name"] == "Linha alheia" for row in supabase.rows)
    queries = [urlsplit(request.full_url).query for request in supabase.requests if request.get_method() != "POST"]
    assert queries and all("owner_id=eq." in query for query in queries)


def test_falha_do_supabase_nao_expoe_a_chave(admin_secrets, monkeypatch):
    monkeypatch.setattr(budget_store, "_storage_config",
        lambda: {"url": FAKE_URL, "key": FAKE_KEY, "table": "saved_budgets"})

    def recusa(request, timeout=None):
        raise HTTPError(request.full_url, 401, "Unauthorized", {}, io.BytesIO(b'{"message":"Invalid API key"}'))

    monkeypatch.setattr(budget_store, "urlopen", recusa)
    user = _login()
    with pytest.raises(RuntimeError) as error:
        budget_store.list_budgets(user.user_id, user)
    assert FAKE_KEY not in str(error.value)


def test_sqlite_preserva_carteira_apos_sair_entrar_e_reiniciar(admin_secrets, monkeypatch, tmp_path):
    monkeypatch.setattr(budget_store, "_storage_config", lambda: {"url": "", "key": "", "table": "saved_budgets"})
    monkeypatch.setenv("RAILPARAMETRIC_BUDGET_DB", str(tmp_path / "carteira.sqlite3"))
    user = _login()
    assert budget_store.storage_mode(user) == "sqlite"
    budget_store.save_budget(user, "Linha Leste", "Ferrovia de passageiro", RESULT)

    _logout()
    user = _login()
    assert [row["name"] for row in budget_store.list_budgets(user.user_id, user)] == ["Linha Leste"]

    st.session_state.clear()
    reloaded = importlib.reload(budget_store)
    monkeypatch.setattr(reloaded, "_storage_config", lambda: {"url": "", "key": "", "table": "saved_budgets"})
    user = _login()
    rows = reloaded.list_budgets(user.user_id, user)
    assert [row["name"] for row in rows] == ["Linha Leste"]
    assert rows[0]["result_json"] == RESULT


def test_acesso_de_teste_nao_grava_e_nao_ve_a_carteira_do_root(admin_secrets, supabase):
    root = _login()
    budget_store.save_budget(root, "Carteira do root", "VLT", RESULT)
    demo = auth.UserContext("demo-teste", "teste@railparametric.local", "Visitante", "test", "local")
    with pytest.raises(PermissionError):
        budget_store.save_budget(demo, "Tentativa", "VLT", RESULT)
    assert budget_store.list_budgets(demo.user_id, demo) == []
