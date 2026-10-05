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


ROOT_EMAIL = "pokermarcky90@gmail.com"
DEMO_USER = "teste"
DEMO_PASSWORD_HASH = sha256(b"teste12345").hexdigest()


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
    backups = access.get("backup_root_emails", []) if access else []
    if isinstance(backups, str):
        backups = [backups]
    return {ROOT_EMAIL, *(str(email).strip().lower() for email in backups)}


def _google_user():
    try:
        if not st.user.is_logged_in:
            return None
        email = str(getattr(st.user, "email", "")).strip().lower()
        if not email:
            return None
        role = "root" if email in _root_emails() else "user"
        name = str(getattr(st.user, "name", "") or email.split("@", 1)[0])
        return UserContext(_identity(email), email, name, role, "google")
    except (AttributeError, KeyError, RuntimeError):
        return None


def _local_user():
    payload = st.session_state.get("local_auth")
    if not isinstance(payload, dict):
        return None
    if payload.get("role") == "test":
        return UserContext("demo-teste", "teste@railparametric.local", "Visitante de teste", "test", "local")
    if payload.get("role") == "root" and payload.get("verified") is True:
        return UserContext("root-emergencia", ROOT_EMAIL, "Administrador (recuperação)", "root", "recovery")
    return None


def _test_environment_user():
    if os.environ.get("RAILPARAMETRIC_TEST_MODE") == "1":
        return UserContext("test-suite-root", ROOT_EMAIL, "Testes automatizados", "root", "test-suite")
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
            st.session_state.local_auth = {"role": "test"}
            st.rerun()
        st.error("Login ou senha de teste inválidos.")


def _recovery_login():
    access = _secrets_section("access")
    expected = str(access.get("emergency_password_hash", "")) if access else ""
    if not expected:
        st.caption("O acesso emergencial será habilitado após a chave de recuperação ser cadastrada nos Secrets.")
        return
    locked_until = float(st.session_state.get("recovery_locked_until", 0))
    if locked_until > time.time():
        remaining = int(locked_until - time.time()) + 1
        st.error(f"Acesso emergencial temporariamente bloqueado. Tente novamente em {remaining} segundos.")
        return
    with st.form("recovery_login_form", clear_on_submit=True):
        recovery_user = st.text_input("Usuário de recuperação")
        recovery_password = st.text_input("Chave de recuperação", type="password")
        submitted = st.form_submit_button("Acessar recuperação", use_container_width=True)
    if submitted:
        supplied = sha256(recovery_password.encode("utf-8")).hexdigest()
        if hmac.compare_digest(recovery_user.strip().lower(), "root") and hmac.compare_digest(supplied, expected):
            st.session_state.pop("recovery_attempts", None)
            st.session_state.pop("recovery_locked_until", None)
            st.session_state.local_auth = {"role": "root", "verified": True}
            st.rerun()
        attempts = int(st.session_state.get("recovery_attempts", 0)) + 1
        st.session_state.recovery_attempts = attempts
        if attempts >= 5:
            st.session_state.recovery_attempts = 0
            st.session_state.recovery_locked_until = time.time() + 300
        st.error("Credenciais de recuperação inválidas.")


def require_user():
    """Retorna o usuário autenticado ou encerra a execução na tela de acesso."""
    user = _test_environment_user() or _local_user() or _google_user()
    if user:
        return user

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
                st.info("A conexão Google está aguardando a configuração segura das credenciais de implantação.")
        with demo_tab:
            st.markdown("**Acesso temporário de demonstração**")
            st.caption("Permite conhecer e calcular. Não permite uploads, troca de bases ou geração de Excel.")
            _demo_login()
        with st.expander("Recuperação administrativa", expanded=False):
            st.caption("Use somente se o acesso Google do administrador estiver indisponível.")
            _recovery_login()
    st.stop()


def logout(user):
    if user.provider == "google":
        st.logout()
    st.session_state.pop("local_auth", None)
    st.session_state.pop("results", None)
    st.session_state.pop("display_results", None)
    st.rerun()
