"""Leitura, validação e aplicação de bases de referência enviadas pelo usuário."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import re
import unicodedata

import pandas as pd


SOURCES = ("SIEC", "SINAPI", "SIURB", "SICRO")
KINDS = ("Insumos", "Serviços")


def _plain(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return re.sub(r"[^a-z0-9]+", " ", text.encode("ascii", "ignore").decode().lower()).strip()


ALIASES = {
    "code": ("codigo", "cod", "item", "codigo do item", "codigo composicao", "codigo insumo"),
    "description": ("descricao", "descricao do item", "servico", "insumo", "denominacao"),
    "unit": ("unidade", "unid", "und", "un"),
    "price": ("preco", "preco unitario", "custo unitario", "valor unitario", "valor", "preco mediano"),
    "date": ("data base", "data", "referencia", "competencia", "mes referencia"),
}


def _find_columns(frame: pd.DataFrame) -> dict[str, str]:
    normalized = {_plain(column): str(column) for column in frame.columns}
    found = {}
    for field, aliases in ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                found[field] = normalized[alias]
                break
        if field not in found:
            for normalized_name, original in normalized.items():
                if any(alias in normalized_name for alias in aliases if len(alias) > 3):
                    found[field] = original
                    break
    return found


def _number(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = re.sub(r"[^0-9,.-]", "", str(value).strip())
    if not text:
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif text.count(".") > 1:
        text = text.replace(".", "")
    try:
        return float(text)
    except ValueError:
        return None


def _read(raw: bytes, filename: str) -> pd.DataFrame:
    if filename.lower().endswith(".csv"):
        for encoding in ("utf-8-sig", "latin-1"):
            try:
                return pd.read_csv(BytesIO(raw), sep=None, engine="python", dtype=str, encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("Codificação CSV não reconhecida.")
    workbook = pd.ExcelFile(BytesIO(raw), engine="openpyxl")
    frames = [pd.read_excel(workbook, sheet_name=name, dtype=str) for name in workbook.sheet_names]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        raise ValueError("A planilha não contém linhas de dados.")
    return max(frames, key=lambda frame: len(frame.index))


@dataclass
class ReferenceBase:
    source: str
    kind: str
    period: str
    filename: str
    digest: str
    records: list[dict]
    columns: list[str]

    @property
    def count(self) -> int:
        return len(self.records)


def parse_reference(raw: bytes, filename: str, source: str, kind: str, period: str) -> ReferenceBase:
    if source not in SOURCES or kind not in KINDS:
        raise ValueError("Fonte ou tipo de tabela inválido.")
    if not raw:
        raise ValueError("O arquivo está vazio.")
    frame = _read(raw, filename)
    columns = _find_columns(frame)
    required = {"code", "description", "unit", "price"}
    missing = required - set(columns)
    if missing:
        labels = {"code": "Código", "description": "Descrição", "unit": "Unidade", "price": "Preço"}
        raise ValueError("Colunas obrigatórias não identificadas: " + ", ".join(labels[x] for x in sorted(missing)))
    records = []
    for _, row in frame.iterrows():
        code = str(row[columns["code"]]).strip() if not pd.isna(row[columns["code"]]) else ""
        unit = str(row[columns["unit"]]).strip() if not pd.isna(row[columns["unit"]]) else ""
        price = _number(row[columns["price"]])
        if not code or not unit or price is None:
            continue
        description = str(row[columns["description"]]).strip() if not pd.isna(row[columns["description"]]) else ""
        row_period = period
        if "date" in columns and not pd.isna(row[columns["date"]]):
            row_period = str(row[columns["date"]]).strip() or period
        records.append({"code": code, "description": description, "unit": unit,
                        "price": price, "date": row_period})
    if not records:
        raise ValueError("Nenhuma linha válida com código, unidade e preço foi encontrada.")
    return ReferenceBase(source, kind, period.strip(), filename, sha256(raw).hexdigest(), records,
                         [str(column) for column in frame.columns])


def apply_reference_bases(catalog: dict, bases: dict[tuple[str, str], ReferenceBase]):
    """Substitui por código as referências já vinculadas às regras e acrescenta o restante ao catálogo."""
    updated = {key: dict(value) for key, value in catalog.items()}
    linked = {}
    for slot, base in bases.items():
        index = {record["code"].strip().upper(): record for record in base.records}
        matches = 0
        for key, item in list(updated.items()):
            if item.get("source") != base.source or item.get("kind") != base.kind:
                continue
            record = index.get(str(item.get("code", "")).strip().upper())
            if not record:
                continue
            updated[key] = {**item, **record, "date": base.period or record["date"],
                            "reference": base.filename,
                            "provenance": f"Upload ativo: {base.filename}"}
            matches += 1
        for record in base.records:
            canonical = f'{base.source}|{base.kind}|{base.period}|{record["code"]}'
            updated.setdefault(canonical, {**record, "key": canonical, "source": base.source,
                                           "kind": base.kind, "status": "upload",
                                           "reference": base.filename,
                                           "provenance": f"Upload ativo: {base.filename}"})
        linked[slot] = matches
    return updated, linked


def embedded_inventory(catalog: dict) -> dict[tuple[str, str], dict]:
    inventory = {}
    for item in catalog.values():
        slot = (item["source"], item["kind"])
        entry = inventory.setdefault(slot, {"periods": set(), "count": 0})
        entry["periods"].add(str(item.get("date") or "Sem data-base"))
        entry["count"] += 1
    return inventory
