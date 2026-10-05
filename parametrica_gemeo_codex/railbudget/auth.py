"""Autenticação e autorização do RailParametric.

O Google confirma a identidade. As permissões são sempre decididas pelo app.
O perfil de demonstração é deliberadamente limitado e não possui privilégios.
"""
from dataclasses import dataclass
from hashlib import sha256
import hmac
import os
import time

import streamlit as st


DEMO_USER = "teste"
DEMO_PASSWORD_HASH = sha256(b"teste12345").hexdigest()
DEMO_SESSION_TTL_SECONDS = 60 * 60


@dataclass(frozen=True)
class UserContext:
    user_id: str
    email: str
    name: str
    role: str
    provider: str


PERMISSIONS = {
    "root": frozenset({"calculate", "download_excel", "manage_bases", "save_budgets"}),
    "user": frozenset({"calculate", "download_excel", "save_budgets"}),
    "test": frozenset({"calculate", "save_budgets"}),
}


def can(user, permission):
    return permission in PERMISSIONS.get(user.role, frozenset())


def _identity(value):
    return sha256(value.strip().lower().encode("utf-8")).hexdigest()[:24]


def _secrets_section(name):
    try:
        return st.secrets.get(name, {})
    except (FileNotFoundError, KeyError):
        return {}


def google_configured():
    auth = _secrets_section("auth")
    return bool(auth and ("google" in auth or all(key in auth for key in
        ("client_id", "client_secret", "server_metadata_url"))))


def _root_emails():
    access = _secrets_section("access")
    values = access.get("root_emails", []) if access else []
    if isinstance(values, str):
        values = [values]
    return {str(email).strip().lower() for email in values if str(email).strip()}


def _regular_access_allowed(email):
    access = _secrets_section("access")
    if not access:
        return False
    if bool(access.get("allow_all_google_users", False)):
        return True
    allowed = access.get("allowed_emails", [])
    domains = access.get("allowed_domains", [])
    if isinstance(allowed, str):allowed=[allowed]
    if isinstance(domains, str):domains=[domains]
    allowed = {str(value).strip().lower() for value in allowed}
    domains = {str(value).strip().lower().lstrip("@") for value in domains}
    return email in allowed or ("@" in email and email.rsplit("@", 1)[1] in domains)


def _google_user():
    try:
        if not st.user.is_logged_in:
            return None
        email = str(getattr(st.user, "email", "")).strip().lower()
        if not email:
            return None
        role = "root" if email in _root_emails() else "user" if _regular_access_allowed(email) else "unauthorized"
        name = str(getattr(st.user, "name", "") or email.split("@", 1)[0])
        return UserContext(_identity(email), email, name, role, "google")
    except (AttributeError, KeyError, RuntimeError):
        return None


def _local_user():
    payload = st.session_state.get("local_auth")
    if not isinstance(payload, dict):
        return None
    if payload.get("role") == "test":
        if time.time() - float(payload.get("issued_at", 0)) > DEMO_SESSION_TTL_SECONDS:
            st.session_state.pop("local_auth", None)
            return None
        return UserContext("demo-teste", "teste@railparametric.local", "Visitante de teste", "test", "local")
    return None


def _test_environment_user():
    if os.environ.get("RAILPARAMETRIC_TEST_MODE") == "1":
        return UserContext("test-suite-root", "root@test.invalid", "Testes automatizados", "root", "test-suite")
    return None


def _demo_login():
    with st.form("demo_login_form", clear_on_submit=True):
        username = st.text_input("Login", autocomplete="username")
        password = st.text_input("Senha", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Entrar no modo de demonstração", type="primary", use_container_width=True)
    if submitted:
        valid_user = hmac.compare_digest(username.strip().lower(), DEMO_USER)
        valid_password = hmac.compare_digest(sha256(password.encode("utf-8")).hexdigest(), DEMO_PASSWORD_HASH)
        if valid_user and valid_password:
            st.session_state.local_auth = {"role": "test", "issued_at": time.time()}
            st.rerun()
        st.error("Login ou senha de teste inválidos.")


def require_user():
    """Retorna o usuário autenticado ou encerra a execução na tela de acesso."""
    user = _test_environment_user() or _local_user() or _google_user()
    if user and user.role != "unauthorized":
        return user
    if user and user.role == "unauthorized":
        with st.container(key="login_shell"):
            st.markdown('<span class="login-eyebrow">ACESSO PROTEGIDO</span>',unsafe_allow_html=True)
            st.title("Acesso ainda não autorizado")
            st.caption("Sua identidade Google foi confirmada, mas este e-mail não consta na lista de usuários permitidos.")
            if st.button("Sair e usar outra conta",icon=":material/logout:",type="primary",use_container_width=True):
                st.logout()
        st.stop()

    with st.container(key="login_shell"):
        st.markdown('<span class="login-eyebrow">ACESSO SEGURO</span>', unsafe_allow_html=True)
        st.title("Parametric Rails")
        st.caption("Entre para criar, calcular e organizar seus orçamentos ferroviários.")
        google_tab, demo_tab = st.tabs(["Entrar com Google", "Conhecer o sistema"])
        with google_tab:
            st.markdown("**Acesso de administradores e usuários**")
            st.caption("Sua senha permanece no Google e não é armazenada pelo RailParametric.")
            if google_configured():
                st.button("Entrar com Google", icon=":material/login:", type="primary",
                    use_container_width=True, on_click=st.login, args=("google",))
            else:
                st.button("Entrar com Google",icon=":material/login:",use_container_width=True,disabled=True)
                st.info("Login Google temporariamente indisponível durante a configuração de segurança.")
        with demo_tab:
            st.markdown("**Acesso temporário de demonstração**")
            st.caption("Permite conhecer e calcular. Não permite uploads, troca de bases ou geração de Excel.")
            _demo_login()
    st.stop()


def logout(user):
    if user.provider == "google":
        st.logout()
    st.session_state.pop("local_auth", None)
    st.session_state.pop("results", None)
    st.session_state.pop("display_results", None)
    st.rerun()
