"""Leitura, normalização e aplicação de bases de referência enviadas pelo usuário."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re
import unicodedata

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill


SOURCES = ("SIEC", "SINAPI", "SIURB", "SICRO")
KINDS = ("Insumos", "Serviços")
REQUIRED_FIELDS = {"code", "description", "unit", "price"}


def _plain(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return re.sub(r"[^a-z0-9]+", " ", text.encode("ascii", "ignore").decode().lower()).strip()


ALIASES = {
    "code": (
        "codigo", "cod", "item", "codigo item", "codigo do item", "codigo composicao",
        "codigo da composicao", "codigo insumo", "codigo do insumo", "codigo servico",
        "codigo do servico", "cod insumo", "cod servico", "cd insumo", "cd servico",
        "referencia",
    ),
    "description": (
        "descricao", "descricao item", "descricao do item", "descricao insumo",
        "descricao do insumo", "descricao servico", "descricao do servico", "discriminacao",
        "denominacao", "tx descricao", "servico", "insumo", "componente",
    ),
    "unit": ("unidade", "unid medida", "un medida", "sg unidade", "unid", "und", "un"),
    "price": (
        "preco unitario", "custo unitario de referencia", "custo unitario", "custo total",
        "valor unitario", "preco mediano", "vl preco unitario", "vl custo unitario",
        "preco", "custo", "valor",
    ),
    "date": (
        "data base", "mes ano", "mes de referencia", "data", "referencia", "competencia",
        "mes referencia",
    ),
}


def _find_columns(frame: pd.DataFrame) -> dict[str, object]:
    normalized = {_plain(column): column for column in frame.columns if _plain(column)}
    found = {}
    for field, aliases in ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                found[field] = normalized[alias]
                break
        if field not in found:
            matches = [
                (len(alias), original)
                for normalized_name, original in normalized.items()
                for alias in aliases
                if len(alias) > 3 and alias in normalized_name
            ]
            if matches:
                found[field] = max(matches, key=lambda pair: pair[0])[1]
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


def _code(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).strip()
    return re.sub(r"\.0$", "", text) if re.fullmatch(r"\d+\.0", text) else text


def _sheet_frames(raw: bytes, filename: str) -> list[tuple[str, pd.DataFrame]]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        for encoding in ("utf-8-sig", "latin-1"):
            try:
                frame = pd.read_csv(
                    BytesIO(raw), sep=None, engine="python", header=None, dtype=object,
                    encoding=encoding, on_bad_lines="skip",
                )
                return [("CSV", frame)]
            except UnicodeDecodeError:
                continue
        raise ValueError("Codificação CSV não reconhecida.")
    if suffix not in {".xlsx", ".xlsm", ".xls"}:
        raise ValueError("Formato não aceito. Envie CSV, XLS, XLSX ou XLSM.")
    engine = "xlrd" if suffix == ".xls" else "openpyxl"
    try:
        workbook = pd.ExcelFile(BytesIO(raw), engine=engine)
    except ImportError as exc:
        raise ValueError(f"Não foi possível abrir {suffix}: dependência de leitura indisponível.") from exc
    frames = []
    for name in workbook.sheet_names:
        frame = pd.read_excel(workbook, sheet_name=name, header=None, dtype=object)
        if not frame.dropna(how="all").empty:
            frames.append((str(name), frame))
    if not frames:
        raise ValueError("A planilha não contém linhas de dados.")
    return frames


def _header_names(frame: pd.DataFrame, row: int, span: int) -> list[str]:
    names = []
    occurrences = {}
    for column in frame.columns:
        parts = []
        for offset in range(span):
            value = frame.iloc[row + offset, column]
            if not pd.isna(value) and str(value).strip():
                part = str(value).strip()
                if part not in parts:
                    parts.append(part)
        name = " ".join(parts) or f"Coluna {column + 1}"
        occurrences[name] = occurrences.get(name, 0) + 1
        names.append(name if occurrences[name] == 1 else f"{name} {occurrences[name]}")
    return names


def _find_table(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]] | None:
    """Localiza cabeçalho de uma ou duas linhas no início de uma aba oficial."""
    best = None
    limit = min(len(frame.index), 80)
    for row in range(limit):
        for span in (1, 2):
            if row + span >= len(frame.index):
                continue
            names = _header_names(frame, row, span)
            columns = _find_columns(pd.DataFrame(columns=names))
            score = len(REQUIRED_FIELDS.intersection(columns)) * 10 + int("date" in columns)
            if best is None or score > best[0]:
                best = (score, row, span, names, columns)
    if best is None or not REQUIRED_FIELDS.issubset(best[4]):
        return None
    _, row, span, names, columns = best
    table = frame.iloc[row + span:].copy()
    table.columns = names
    return table.dropna(how="all"), columns


@dataclass
class ReferenceBase:
    source: str
    kind: str
    period: str
    filename: str
    digest: str
    records: list[dict]
    columns: list[str]
    sheets: list[str]

    @property
    def count(self) -> int:
        return len(self.records)


def parse_reference(raw: bytes, filename: str, source: str, kind: str, period: str) -> ReferenceBase:
    if source not in SOURCES or kind not in KINDS:
        raise ValueError("Fonte ou tipo de tabela inválido.")
    if not raw:
        raise ValueError("O arquivo está vazio.")
    sheet_frames = _sheet_frames(raw, filename)
    parsed_sheets = []
    all_columns = []
    records_by_code = {}
    for sheet_name, raw_frame in sheet_frames:
        located = _find_table(raw_frame)
        if not located:
            continue
        frame, columns = located
        parsed_sheets.append(sheet_name)
        all_columns.extend(str(column) for column in frame.columns)
        for _, row in frame.iterrows():
            code = _code(row[columns["code"]])
            unit = "" if pd.isna(row[columns["unit"]]) else str(row[columns["unit"]]).strip()
            price = _number(row[columns["price"]])
            if not code or not unit or price is None:
                continue
            description = "" if pd.isna(row[columns["description"]]) else str(row[columns["description"]]).strip()
            row_period = period.strip()
            if "date" in columns and not pd.isna(row[columns["date"]]):
                row_period = str(row[columns["date"]]).strip() or row_period
            records_by_code[code.strip().upper()] = {
                "code": code, "description": description, "unit": unit,
                "price": price, "date": row_period,
            }
    if not parsed_sheets:
        checked = ", ".join(name for name, _ in sheet_frames)
        raise ValueError(
            "Colunas obrigatórias não identificadas. Não localizei um cabeçalho com Código, "
            "Descrição, Unidade e Preço nas abas: " + checked + "."
        )
    if not records_by_code:
        raise ValueError("Nenhuma linha válida com código, unidade e preço foi encontrada.")
    return ReferenceBase(
        source, kind, period.strip(), filename, sha256(raw).hexdigest(),
        list(records_by_code.values()), list(dict.fromkeys(all_columns)), parsed_sheets,
    )


def normalized_excel(base: ReferenceBase) -> bytes:
    """Converte a base ativa em uma planilha simples, auditável e reutilizável."""
    rows = [{
        "Fonte": base.source, "Tipo": base.kind, "Código": record["code"],
        "Descrição": record["description"], "Unidade": record["unit"],
        "Preço": record["price"], "Data-base": record["date"] or base.period,
    } for record in base.records]
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name="Base normalizada", index=False)
        sheet = writer.book["Base normalizada"]
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for cell in sheet[1]:
            cell.font = Font(color="FFFFFF", bold=True)
            cell.fill = PatternFill("solid", fgColor="173D3A")
            cell.alignment = Alignment(horizontal="center")
        widths = {"A": 12, "B": 14, "C": 20, "D": 72, "E": 14, "F": 20, "G": 16}
        for column, width in widths.items():
            sheet.column_dimensions[column].width = width
        for cell in sheet["F"][1:]:
            cell.number_format = '[$R$-pt-BR] #,##0.00'
    return output.getvalue()


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
