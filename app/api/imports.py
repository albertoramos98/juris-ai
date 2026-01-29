# app/api/imports.py
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.permissions.dependencies import ensure_office_not_blocked

from app.models.user import User
from app.schemas.imports import ImportPreviewResponse, ImportCommitResponse, ImportErrorItem

from app.services.import_processes_service import (
    parse_csv_bytes,
    validate_rows,
    commit_rows,
)

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/processes/preview", response_model=ImportPreviewResponse)
async def preview_processes_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Envie um arquivo .csv")

    content = await file.read()
    headers, rows = parse_csv_bytes(content)

    if not headers:
        raise HTTPException(status_code=400, detail="CSV vazio ou inválido")

    valid_rows, errors = validate_rows(headers, rows)

    # sample (primeiras 20 linhas) pra render no frontend
    sample = rows[:20]

    return {
        "columns": headers,
        "sample": sample,
        "total_rows": len(rows),
        "valid_rows": len(valid_rows),
        "error_rows": len(rows) - len(valid_rows),
        "errors": [ImportErrorItem(**e) for e in errors],
    }


@router.post("/processes/commit", response_model=ImportCommitResponse)
async def commit_processes_import(
    file: UploadFile = File(...),
    mode: str = Query(default="create_only", pattern="^(create_only|upsert)$"),
    db: Session = Depends(get_db),
    user: User = Depends(ensure_office_not_blocked),
):
    """
    mode:
      - create_only: cria só se não existir; se existir, retorna erro por linha
      - upsert: se existir, atualiza (court/type/status/client)
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Envie um arquivo .csv")

    content = await file.read()
    headers, rows = parse_csv_bytes(content)

    if not headers:
        raise HTTPException(status_code=400, detail="CSV vazio ou inválido")

    valid_rows, validation_errors = validate_rows(headers, rows)

    # se faltar coluna obrigatória, a validação retorna erro no row=0
    missing_cols_errors = [e for e in validation_errors if e.get("row") == 0]
    if missing_cols_errors:
        return {
            "total_rows": len(rows),
            "created": 0,
            "updated": 0,
            "failed": len(rows),
            "errors": [ImportErrorItem(**e) for e in validation_errors],
        }

    created, updated, failed_commit, commit_errors = commit_rows(
        db=db,
        rows=valid_rows,
        office_id=user.office_id,
        mode=mode,
    )

    # erros totais = erros de validação (linhas inválidas) + erros de commit (linhas válidas que falharam)
    invalid_count = len(rows) - len(valid_rows)

    all_errors = []
    for e in validation_errors:
        if e.get("row") != 0:  # ignora missing cols aqui pq já tratamos acima
            all_errors.append(e)
    all_errors.extend(commit_errors)

    return {
        "total_rows": len(rows),
        "created": created,
        "updated": updated,
        "failed": invalid_count + failed_commit,
        "errors": [ImportErrorItem(**e) for e in all_errors],
    }
