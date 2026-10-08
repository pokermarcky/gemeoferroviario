"""Persistência da última base de referência ativa por fonte e tipo."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import zlib

from railbudget.auth import can
from railbudget.reference_data import KINDS, SOURCES, ReferenceBase


def _reference_db_path():
    configured=os.environ.get("RAILPARAMETRIC_REFERENCE_DB", "").strip()
    if configured:return Path(configured)
    return Path(__file__).resolve().parents[1]/".runtime"/"reference_bases.sqlite3"


def _connection():
    path=_reference_db_path();path.parent.mkdir(parents=True,exist_ok=True)
    try:path.parent.chmod(0o700)
    except OSError:pass
    connection=sqlite3.connect(path,timeout=20)
    connection.row_factory=sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("""CREATE TABLE IF NOT EXISTS active_reference_bases (
        source TEXT NOT NULL, kind TEXT NOT NULL, period TEXT NOT NULL,
        filename TEXT NOT NULL, digest TEXT NOT NULL, payload BLOB NOT NULL,
        updated_at TEXT NOT NULL, PRIMARY KEY (source, kind)
    )""")
    connection.commit()
    try:path.chmod(0o600)
    except OSError:pass
    return connection


def _payload(base):
    document={"records":base.records,"columns":base.columns,"sheets":base.sheets}
    return zlib.compress(json.dumps(document,ensure_ascii=False,separators=(",",":")).encode("utf-8"),9)


def save_reference_base(user,base):
    """Substitui a versão anterior somente quando o usuário pode gerir bases."""
    if not can(user,"manage_bases"):
        raise PermissionError("Somente o administrador root pode substituir a data-base.")
    if base.source not in SOURCES or base.kind not in KINDS:
        raise ValueError("Fonte ou tipo de base inválido.")
    try:
        with _connection() as connection:
            connection.execute("""INSERT INTO active_reference_bases
                (source,kind,period,filename,digest,payload,updated_at)
                VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(source,kind) DO UPDATE SET
                period=excluded.period,filename=excluded.filename,digest=excluded.digest,
                payload=excluded.payload,updated_at=excluded.updated_at""",(
                base.source,base.kind,base.period,base.filename,base.digest,_payload(base),
                datetime.now(timezone.utc).isoformat(),
            ))
            connection.commit()
    except sqlite3.Error as exc:
        raise RuntimeError("Não foi possível preservar a nova data-base.") from exc


def load_reference_bases():
    """Carrega somente a versão mais recente de cada combinação fonte/tipo."""
    try:
        with _connection() as connection:
            rows=connection.execute("SELECT * FROM active_reference_bases").fetchall()
    except sqlite3.Error:
        return {}
    bases={}
    for row in rows:
        try:
            document=json.loads(zlib.decompress(row["payload"]).decode("utf-8"))
            base=ReferenceBase(row["source"],row["kind"],row["period"],row["filename"],
                row["digest"],document["records"],document["columns"],document["sheets"])
            bases[(base.source,base.kind)]=base
        except (KeyError,TypeError,ValueError,json.JSONDecodeError,zlib.error):
            continue
    return bases
