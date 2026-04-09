from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.process import Process
from app.services.rag_service import (
    index_process,
    query_process,
    compose_process,
    generate_petition_draft,
)

from fastapi.responses import StreamingResponse
from app.services.document_generator_service import generate_docx_from_text

from app.permissions.dependencies import ensure_office_not_blocked

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/export-docx")
def rag_export_docx(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(ensure_office_not_blocked),
):
    """
    Exporta a petição usando MAPEAMENTO INTELIGENTE.
    Identifica o que trocar no modelo original sem precisar de marcadores {{...}}.
    Mantém 100% da formatação original (réplica perfeita).
    """
    process_id = payload.get("process_id")
    mode = payload.get("mode", "attack")
    notes = payload.get("notes", "")

    if not process_id:
        raise HTTPException(status_code=400, detail="process_id é obrigatório.")

    # 1. Determina o caminho do modelo original
    import os
    if mode == "attack":
        template_path = os.path.join(os.getcwd(), "MODELOS DE INICIAIS", "inicial Elton Claudino x Fruta Nobre.docx")
    else:
        template_path = os.path.join(os.getcwd(), "MODELOS CONTESTASÇÃO EMPRESA", "ação nb x sandro julio CIVIL.docx")

    # 2. Extrai o texto do modelo para a IA mapear
    from app.services.document_extractor import extract_text
    with open(template_path, "rb") as f:
        template_bytes = f.read()
    template_text = extract_text(template_bytes, "docx")

    # 3. Busca contexto do RAG (Fatos do novo caso)
    from app.services.rag_service import _retrieve_top_chunks
    sources, context_blocks = _retrieve_top_chunks(
        db=db,
        office_id=current_user.office_id,
        process_id=process_id,
        question="Recupere fatos, pedidos e fundamentos para a petição.",
        top_k=15
    )
    case_context = "\n".join(context_blocks)

    # 4. IA mapeia o que trocar no modelo original
    from app.services.openai_service import map_and_replace_template
    proc = db.query(Process).filter(Process.id == process_id).first()
    client_name = proc.client.name if proc and proc.client else "Novo Cliente"
    
    replacements = map_and_replace_template(
        template_text=template_text,
        case_context=case_context,
        client_name=client_name,
        notes=notes
    )

    # 5. Gera o .docx final com substituições cirúrgicas (preservando formatação)
    from app.services.document_generator_service import generate_docx_from_template
    buffer = generate_docx_from_template(template_path, replacements)
    
    filename = f"Peticao_Replica_{process_id}.docx"
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _ensure_process(db: Session, office_id: int, process_id: int):
    p = (
        db.query(Process)
        .filter(Process.id == process_id, Process.office_id == office_id)
        .first()
    )
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found",
        )
    return p


@router.post("/process/{process_id}/index", status_code=status.HTTP_200_OK)
def rag_index(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(ensure_office_not_blocked),
):
    _ensure_process(db, current_user.office_id, process_id)

    result = index_process(
        db=db,
        office_id=current_user.office_id,
        process_id=process_id,
    )

    if not result.get("ok"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error") or "Erro interno na indexação.",
        )

    # Se result['ok'] é True mas indexed é False, significa que apenas não tinha documentos
    # Retornamos 200 para o front mostrar a mensagem de aviso (detail) de forma amigável
    return result


@router.post("/query")
def rag_query(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(ensure_office_not_blocked),
):
    try:
        process_id = int(payload.get("process_id") or 0)
    except Exception:
        process_id = 0

    question = str(payload.get("question") or "").strip()

    try:
        top_k = int(payload.get("top_k") or 6)
    except Exception:
        top_k = 6

    if not process_id or not question:
        raise HTTPException(
            status_code=400,
            detail="process_id e question são obrigatórios.",
        )

    if top_k < 1:
        top_k = 1
    if top_k > 18:
        top_k = 18

    _ensure_process(db, current_user.office_id, process_id)

    result = query_process(
        db=db,
        office_id=current_user.office_id,
        process_id=process_id,
        question=question,
        top_k=top_k,
    )

    if not result.get("ok"):
        raise HTTPException(
            status_code=400,
            detail=result.get("detail") or result.get("error") or "Query failed",
        )

    return result


@router.post("/compose", status_code=status.HTTP_200_OK)
def rag_compose(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(ensure_office_not_blocked),
):
    try:
        process_id = int(payload.get("process_id") or 0)
    except Exception:
        process_id = 0

    mode = str(payload.get("mode") or "").strip().lower()
    style = str(payload.get("style") or "formal").strip().lower()

    try:
        top_k = int(payload.get("top_k") or 10)
    except Exception:
        top_k = 10

    if process_id <= 0 or mode not in ("attack", "defense"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="process_id e mode (attack/defense) são obrigatórios.",
        )

    if top_k < 3:
        top_k = 3
    if top_k > 18:
        top_k = 18

    _ensure_process(db, current_user.office_id, process_id)

    result = compose_process(
        db=db,
        office_id=current_user.office_id,
        process_id=process_id,
        mode=mode,
        style=style,
        top_k=top_k,
        notes=str(payload.get("notes") or "").strip(),
        has_audio=bool(payload.get("has_audio", False)),
        audio_notes=str(payload.get("audio_notes") or "").strip(),
        calculation_value=str(payload.get("calculation_value") or "").strip(),
    )

    if not result.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("detail", "Compose failed"),
        )

    return result


@router.post("/generate-petition")
def rag_generate_petition(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(ensure_office_not_blocked),
):
    try:
        process_id = int(payload.get("process_id") or 0)
    except Exception:
        process_id = 0

    mode = str(payload.get("mode") or "").strip().lower()
    style = str(payload.get("style") or "formal").strip().lower()
    notes = str(payload.get("notes") or "").strip()

    try:
        top_k = int(payload.get("top_k") or 15)
    except Exception:
        top_k = 15

    if process_id <= 0:
        raise HTTPException(status_code=400, detail="process_id é obrigatório.")
    if mode not in {"attack", "defense"}:
        raise HTTPException(status_code=400, detail="mode deve ser 'attack' ou 'defense'.")

    if top_k < 3:
        top_k = 3
    if top_k > 30:
        top_k = 30

    _ensure_process(db, current_user.office_id, process_id)

    result = generate_petition_draft(
        db=db,
        office_id=current_user.office_id,
        process_id=process_id,
        mode=mode,
        style=style,
        top_k=top_k,
        notes=notes,
        has_audio=bool(payload.get("has_audio", False)),
        audio_notes=str(payload.get("audio_notes") or "").strip(),
        calculation_value=str(payload.get("calculation_value") or "").strip(),
    )

    if not result.get("ok"):
        raise HTTPException(
            status_code=400,
            detail=result.get("detail", "Falha ao gerar peça."),
        )

    return result