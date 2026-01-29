import csv
import io
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.process import Process

# Campos obrigatórios e opcionais do CSV
REQUIRED_COLUMNS = ["number", "client_name", "court", "type"]
OPTIONAL_COLUMNS = ["status"]


def _normalize_key(s: str) -> str:
    return (s or "").strip().lower()


def _normalize_value(v: Any) -> str:
    return str(v).strip() if v is not None else ""


def parse_csv_bytes(content: bytes) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Lê bytes do CSV, tenta utf-8 e fallback latin-1,
    retorna headers normalizados + linhas normalizadas
    """
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    f = io.StringIO(text)
    reader = csv.DictReader(f)

    if not reader.fieldnames:
        return [], []

    raw_headers = [h for h in reader.fieldnames if h is not None]
    headers = [_normalize_key(h) for h in raw_headers]

    rows: List[Dict[str, str]] = []
    for r in reader:
        row: Dict[str, str] = {}
        for raw_h, norm_h in zip(raw_headers, headers):
            row[norm_h] = _normalize_value(r.get(raw_h))
        rows.append(row)

    return headers, rows


def validate_rows(
    headers: List[str],
    rows: List[Dict[str, str]],
) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    """
    Valida colunas obrigatórias e dados linha a linha.
    Retorna:
      - rows válidas
      - lista de erros (row, field, message)
    """
    errors: List[Dict[str, Any]] = []
    valid_rows: List[Dict[str, str]] = []

    # valida colunas obrigatórias
    for col in REQUIRED_COLUMNS:
        if col not in headers:
            errors.append({
                "row": 0,
                "field": col,
                "message": f"Coluna obrigatória ausente: {col}"
            })

    if errors:
        return [], errors

    seen_numbers = set()

    for idx, row in enumerate(rows, start=1):
        row_ok = True

        for col in REQUIRED_COLUMNS:
            if not row.get(col):
                errors.append({
                    "row": idx,
                    "field": col,
                    "message": "Campo obrigatório vazio"
                })
                row_ok = False

        number = row.get("number")
        if number:
            if number in seen_numbers:
                errors.append({
                    "row": idx,
                    "field": "number",
                    "message": "Número de processo duplicado no CSV"
                })
                row_ok = False
            else:
                seen_numbers.add(number)

        if row_ok:
            valid_rows.append(row)

    return valid_rows, errors


def commit_rows(
    db: Session,
    rows: List[Dict[str, str]],
    office_id: int,
    mode: str = "create_only",  # ou upsert
) -> Tuple[int, int, int, List[Dict[str, Any]]]:
    """
    Persiste os dados no banco.
    Retorna: created, updated, failed, errors
    """
    created = 0
    updated = 0
    failed = 0
    errors: List[Dict[str, Any]] = []

    for idx, row in enumerate(rows, start=1):
        try:
            # cliente: cria se não existir
            client = (
                db.query(Client)
                .filter(
                    Client.name == row["client_name"],
                    Client.office_id == office_id,
                )
                .first()
            )

            if not client:
                client = Client(
                    name=row["client_name"],
                    document=None,
                    office_id=office_id,
                )
                db.add(client)
                db.flush()  # pega ID sem commit

            process = (
                db.query(Process)
                .filter(
                    Process.number == row["number"],
                    Process.office_id == office_id,
                )
                .first()
            )

            if process:
                if mode == "upsert":
                    process.court = row["court"]
                    process.type = row["type"]
                    process.status = row.get("status") or process.status
                    process.client_id = client.id
                    updated += 1
                else:
                    failed += 1
                    errors.append({
                        "row": idx,
                        "field": "number",
                        "message": "Processo já existe"
                    })
                    continue
            else:
                process = Process(
                    number=row["number"],
                    court=row["court"],
                    type=row["type"],
                    status=row.get("status") or "ativo",
                    client_id=client.id,
                    office_id=office_id,
                )
                db.add(process)
                created += 1

        except Exception as e:
            db.rollback()
            failed += 1
            errors.append({
                "row": idx,
                "field": "general",
                "message": str(e),
            })

    db.commit()
    return created, updated, failed, errors
