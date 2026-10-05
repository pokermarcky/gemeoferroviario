"""Persistência dos orçamentos por usuário.

Quando Supabase está configurado, os dados sobrevivem a reinicializações do
Streamlit Cloud. Sem configuração, uma área temporária de sessão mantém o fluxo
utilizável para desenvolvimento e demonstração.
"""
from datetime import datetime, timezone
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

import streamlit as st


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
    config = _storage_config()
    return bool(config["url"] and config["key"])


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


def list_budgets(user_id):
    if persistent_storage_enabled():
        owner = quote(user_id, safe="")
        return _request("GET", f"?owner_id=eq.{owner}&select=*&order=created_at.desc")
    return [row for row in reversed(_session_rows()) if row["owner_id"] == user_id]


def save_budget(user, name, modality, result):
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
    if persistent_storage_enabled():
        saved = _request("POST", "", row)
        return saved[0] if saved else row
    _session_rows().append(row)
    return row

