from __future__ import annotations

from annotated_types import doc
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.services.email_flow_service import stop_email_flows_on_document_upload

from app.core.database import get_db
from app.auth.dependencies import get_current_user

from app.models.process import Process
from app.models.document import Document
from app.schemas.document import DocumentOut

from app.services.google_drive_service import (
    ensure_process_folder,
    ensure_category_folder,
    upload_file,
    CATEGORY_FOLDERS,
)
from app.services.google_oauth import get_valid_access_token

router = APIRouter(prefix="/processes", tags=["Documents"])


def _validate_category(category: str) -> str:
    c = (category or "").strip().lower()
    if c not in CATEGORY_FOLDERS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid category. Use one of: {', '.join(CATEGORY_FOLDERS.keys())}",
        )
    return c


@router.get("/{process_id}/documents", response_model=List[DocumentOut])
def list_documents(
    process_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    proc = (
        db.query(Process)
        .filter(Process.id == process_id, Process.office_id == user.office_id)
        .first()
    )
    if not proc:
        raise HTTPException(status_code=404, detail="Process not found")

    docs = (
        db.query(Document)
        .filter(Document.process_id == process_id, Document.office_id == user.office_id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return docs


@router.post("/{process_id}/documents/upload", response_model=DocumentOut)
async def upload_document(
    process_id: int,
    category: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    category = _validate_category(category)

    proc = (
        db.query(Process)
        .filter(Process.id == process_id, Process.office_id == user.office_id)
        .first()
    )
    if not proc:
        raise HTTPException(status_code=404, detail="Process not found")

    access_token = get_valid_access_token(db, user.office_id)

    # 1) garante pasta raiz do processo no Drive
    if not proc.drive_folder_id:
        # monta um nome estável e curto (sem title, pq teu model não tem)
        proc_number = (getattr(proc, "number", None) or getattr(proc, "process_number", None) or "").strip()
        name_suffix = proc_number[:80] if proc_number else f"id_{proc.id}"
        folder_name = f"Processo_{proc.id}_{name_suffix}"

        folder = ensure_process_folder(access_token=access_token, folder_name=folder_name)

        proc.drive_folder_id = folder["id"]
        db.add(proc)
        db.commit()
        db.refresh(proc)

    # 2) garante subpasta por categoria
    category_folder = ensure_category_folder(
        access_token=access_token,
        process_folder_id=proc.drive_folder_id,
        category_key=category,
    )

    # 3) upload do arquivo na subpasta
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    mime_type = file.content_type or "application/octet-stream"

    uploaded = upload_file(
        access_token=access_token,
        folder_id=category_folder["id"],
        file_bytes=file_bytes,
        file_name=file.filename or "arquivo",
        mime_type=mime_type,
    )

    # 4) salva no banco
    doc = Document(
        office_id=user.office_id,
        process_id=process_id,
        category=category,
        status="uploaded",
        file_name=uploaded.get("name") or file.filename or "arquivo",
        mime_type=uploaded.get("mimeType") or mime_type,
        drive_file_id=uploaded["id"],
        drive_web_view_link=uploaded.get("webViewLink"),



    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 5) STOP automático do flow de cobrança (se existir)
    stopped = stop_email_flows_on_document_upload(
        db=db,
        office_id=user.office_id,
        process_id=process_id,
        reason=f"Documento recebido: {doc.category}",
    )

    if stopped:
        print(f"[EMAIL_FLOW] stopped={stopped} office={user.office_id} process={process_id}")

    return doc




