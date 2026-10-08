"""Persistência dos orçamentos por usuário.

Quando Supabase está configurado, os dados sobrevivem a reinicializações do
Streamlit Cloud. Sem essa configuração, usuários individuais usam SQLite local,
que preserva dados entre logout e login no mesmo servidor. O acesso de teste é
compartilhado e permanece isolado por sessão.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

import streamlit as st

from railbudget.auth import is_primary_root


def _storage_config():
    try:
        section = st.secrets.get("storage", {})
    except (FileNotFoundError, KeyError):
        section = {}
    return {
        "url": str(section.get("supabase_url", "")).rstrip("/"),
        "key": str(section.get("supabase_service_role_key", "")),
        "table": str(section.get("budgets_table", "saved_budgets")),
    }


def persistent_storage_enabled():
    return True


def storage_mode(user=None):
    config = _storage_config()
    if config["url"] and config["key"]:
        return "supabase"
    if user is not None and user.role == "test":
        return "session"
    return "sqlite"


def _local_db_path():
    configured=os.environ.get("RAILPARAMETRIC_BUDGET_DB", "").strip()
    if configured:return Path(configured)
    return Path(__file__).resolve().parents[1]/".runtime"/"user_budgets.sqlite3"


def _sqlite_connection():
    path=_local_db_path();path.parent.mkdir(parents=True,exist_ok=True)
    try:path.parent.chmod(0o700)
    except OSError:pass
    connection=sqlite3.connect(path,timeout=10)
    connection.row_factory=sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("""CREATE TABLE IF NOT EXISTS saved_budgets (
        id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, owner_email TEXT NOT NULL,
        name TEXT NOT NULL, modality TEXT NOT NULL, total REAL NOT NULL,
        result_json TEXT NOT NULL, created_at TEXT NOT NULL
    )""")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_saved_budgets_owner_created ON saved_budgets(owner_id,created_at DESC)")
    connection.commit()
    try:path.chmod(0o600)
    except OSError:pass
    return connection


def _request(method, path, payload=None):
    config = _storage_config()
    url = f'{config["url"]}/rest/v1/{config["table"]}{path}'
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "apikey": config["key"],
        "Authorization": "Bearer " + config["key"],
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=12) as response:
            body = response.read()
            return json.loads(body.decode("utf-8")) if body else []
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError("A base de orçamentos recusou a operação: " + detail[:240]) from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("Não foi possível acessar a base persistente de orçamentos.") from exc


def _session_rows():
    return st.session_state.setdefault("saved_budgets_local", [])


def list_budgets(user_id,user=None):
    mode=storage_mode(user)
    if mode=="supabase":
        owner = quote(user_id, safe="")
        return _request("GET", f"?owner_id=eq.{owner}&select=*&order=created_at.desc")
    if mode=="session":
        return [row for row in reversed(_session_rows()) if row["owner_id"] == user_id]
    with _sqlite_connection() as connection:
        rows=connection.execute("SELECT * FROM saved_budgets WHERE owner_id=? ORDER BY created_at DESC",(user_id,)).fetchall()
    output=[]
    for row in rows:
        item=dict(row)
        try:item["result_json"]=json.loads(item["result_json"])
        except json.JSONDecodeError:item["result_json"]={}
        output.append(item)
    return output


def save_budget(user, name, modality, result):
    if not is_primary_root(user):
        raise PermissionError("Meus Orçamentos está disponível somente para o root principal.")
    row = {
        "id": str(uuid4()),
        "owner_id": user.user_id,
        "owner_email": user.email,
        "name": name.strip(),
        "modality": modality,
        "total": float(result["total"]),
        "result_json": result,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    mode=storage_mode(user)
    if mode=="supabase":
        saved = _request("POST", "", row)
        return saved[0] if saved else row
    if mode=="session":
        _session_rows().append(row)
        return row
    with _sqlite_connection() as connection:
        connection.execute("""INSERT INTO saved_budgets
            (id,owner_id,owner_email,name,modality,total,result_json,created_at)
            VALUES (?,?,?,?,?,?,?,?)""",(
            row["id"],row["owner_id"],row["owner_email"],row["name"],row["modality"],row["total"],
            json.dumps(row["result_json"],ensure_ascii=False),row["created_at"],
        ))
        connection.commit()
    return row
