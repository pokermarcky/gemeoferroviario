"""Autenticação local e autorização do RailParametric.

Credenciais privilegiadas existem somente nos Secrets da implantação. O perfil
de demonstração é deliberadamente limitado e não possui privilégios.
"""
from dataclasses import dataclass
import base64
from hashlib import pbkdf2_hmac, sha256
import hmac
import os
import time

import streamlit as st


DEMO_USER = "teste"
DEMO_PASSWORD_HASH = sha256(b"teste12345").hexdigest()
DEMO_SESSION_TTL_SECONDS = 60 * 60
ADMIN_SESSION_TTL_SECONDS = 8 * 60 * 60
MAX_ADMIN_ATTEMPTS = 5
ADMIN_LOCK_SECONDS = 15 * 60
PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 600_000


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
    "test": frozenset({"calculate", "download_excel_trial", "save_budgets"}),
}


def can(user, permission):
    return permission in PERMISSIONS.get(user.role, frozenset())


def budget_download_limit(user):
    """Quantidade máxima por sessão; ``None`` representa acesso ilimitado."""
    return 1 if can(user, "download_excel_trial") else None


def can_download_budget(user, downloads_used=0):
    return can(user, "download_excel") or (
        can(user, "download_excel_trial") and downloads_used < budget_download_limit(user)
    )


def _identity(value):
    return sha256(value.strip().lower().encode("utf-8")).hexdigest()[:24]


def _secrets_section(name):
    try:
        return st.secrets.get(name, {})
    except (FileNotFoundError, KeyError):
        return {}


def _admin_accounts():
    accounts=[]
    for section_name in ("local_admin", "local_admin_secondary", "local_admin_backup"):
        section=_secrets_section(section_name)
        username=str(section.get("username", "")).strip().lower() if section else ""
        password_hash=str(section.get("password_hash", "")) if section else ""
        if username and password_hash:accounts.append((username,password_hash))
    return accounts


def _verify_password(password, encoded_hash):
    """Valida um hash PBKDF2 versionado sem guardar a senha reversível."""
    try:
        algorithm, iterations, salt_b64, digest_b64 = encoded_hash.split("$", 3)
        if algorithm != PASSWORD_HASH_ALGORITHM:
            return False
        rounds = int(iterations)
        if rounds < PASSWORD_HASH_ITERATIONS:
            return False
        salt = base64.b64decode(salt_b64, validate=True)
        expected = base64.b64decode(digest_b64, validate=True)
        if len(salt) < 16 or len(expected) != 32:
            return False
        supplied = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds, dklen=32)
        return hmac.compare_digest(supplied, expected)
    except (TypeError, ValueError):
        return False


def admin_configured():
    return bool(_admin_accounts())


def _local_user():
    payload = st.session_state.get("local_auth")
    if not isinstance(payload, dict):
        return None
    if payload.get("role") == "test":
        if time.time() - float(payload.get("issued_at", 0)) > DEMO_SESSION_TTL_SECONDS:
            st.session_state.pop("local_auth", None)
            return None
        return UserContext("demo-teste", "teste@railparametric.local", "Visitante de teste", "test", "local")
    if payload.get("role") == "root":
        if time.time() - float(payload.get("issued_at", 0)) > ADMIN_SESSION_TTL_SECONDS:
            st.session_state.pop("local_auth", None)
            return None
        username=str(payload.get("username", "")).strip().lower()
        if any(hmac.compare_digest(username, candidate) for candidate,_ in _admin_accounts()):
            return UserContext(_identity(username),username,"Administrador", "root", "local")
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


def _admin_login():
    locked_until=float(st.session_state.get("admin_locked_until", 0))
    if locked_until > time.time():
        remaining=(int(locked_until-time.time())//60)+1
        st.error(f"Acesso temporariamente bloqueado após tentativas inválidas. Aguarde {remaining} minuto(s).")
        return
    if not admin_configured():
        st.button("Entrar como administrador",icon=":material/admin_panel_settings:",
            use_container_width=True,disabled=True)
        st.info("A conta administrativa está aguardando a configuração privada nos Secrets.")
        return
    with st.form("admin_login_form",clear_on_submit=True):
        username=st.text_input("Login administrativo",autocomplete="username")
        password=st.text_input("Senha",type="password",autocomplete="current-password")
        submitted=st.form_submit_button("Entrar como administrador",type="primary",use_container_width=True)
    if not submitted:return
    supplied_user=username.strip().lower()
    authenticated=any(hmac.compare_digest(supplied_user,candidate) and _verify_password(password,password_hash)
        for candidate,password_hash in _admin_accounts())
    if authenticated:
        st.session_state.pop("admin_attempts",None)
        st.session_state.pop("admin_locked_until",None)
        st.session_state.local_auth={"role":"root","username":supplied_user,"issued_at":time.time()}
        st.rerun()
    attempts=int(st.session_state.get("admin_attempts",0))+1
    st.session_state.admin_attempts=attempts
    if attempts >= MAX_ADMIN_ATTEMPTS:
        st.session_state.admin_attempts=0
        st.session_state.admin_locked_until=time.time()+ADMIN_LOCK_SECONDS
    st.error("Credenciais inválidas.")


def require_user():
    """Retorna o usuário autenticado ou encerra a execução na tela de acesso."""
    user = _test_environment_user() or _local_user()
    if user:return user

    with st.container(key="login_shell"):
        st.markdown('<span class="login-eyebrow">ACESSO SEGURO</span>', unsafe_allow_html=True)
        st.title("Parametric Rails")
        st.caption("Entre para criar, calcular e organizar seus orçamentos ferroviários.")
        admin_tab, demo_tab = st.tabs(["Administrador", "Conhecer o sistema"])
        with admin_tab:
            st.markdown("**Acesso administrativo**")
            st.caption("Credenciais protegidas nos Secrets privados da implantação.")
            _admin_login()
        with demo_tab:
            st.markdown("**Acesso temporário de demonstração**")
            st.caption("Permite conhecer, calcular e baixar um orçamento em Excel por sessão. Não permite uploads nem troca de bases.")
            _demo_login()
    st.stop()


def logout(user):
    st.session_state.pop("local_auth", None)
    st.session_state.pop("results", None)
    st.session_state.pop("display_results", None)
    st.rerun()
