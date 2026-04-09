from __future__ import annotations

import os
import shutil
import tempfile
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user

from app.models.user import User
from app.models.process import Process
from app.models.document import Document
from app.models.client import Client
from app.services.openai_service import transcribe_audio, extract_case_info
from app.services.rag_service import index_process, generate_petition_draft

router = APIRouter(prefix="/meetings", tags=["meetings"])

@router.post("/fast-track")
async def fast_track_meeting(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    FLUXO MÁGICO:
    1. Transcreve Áudio
    2. Extrai Nome do Cliente e Tipo de Ação
    3. Cria Cliente e Processo automaticamente
    4. Indexa e Gera Rascunho de Petição Inicial
    """
    fd, temp_path = tempfile.mkstemp(suffix=".webm")
    os.close(fd)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        text = transcribe_audio(temp_path)
        if not text:
            raise HTTPException(status_code=500, detail="Falha na transcrição.")

        # Extrai info via IA
        info = extract_case_info(text)
        client_name = info.get("client_name") or "Novo Cliente via Áudio"
        
        # 1. Cria ou busca cliente
        client = db.query(Client).filter(Client.name == client_name, Client.office_id == current_user.office_id).first()
        if not client:
            # CORREÇÃO: Removido campo 'phone' que não existe no modelo
            client = Client(name=client_name, office_id=current_user.office_id, email="")
            db.add(client)
            db.commit()
            db.refresh(client)

        # 2. Cria processo
        proc = Process(
            office_id=current_user.office_id,
            client_id=client.id,
            number=f"AUTO-{datetime.now().strftime('%Y%m%d%H%M')}",
            court=info.get("court") or "Tribunal a Definir",
            type=info.get("case_type") or "Ação Cível",
            status="ativo"
        )
        db.add(proc)
        db.commit()
        db.refresh(proc)

        # 3. Salva a transcrição como documento
        doc = Document(
            office_id=proc.office_id,
            process_id=proc.id,
            category="Transcrição de Reunião",
            status="uploaded",
            file_name="transcricao_onboarding.txt",
            mime_type="text/plain",
            drive_file_id=f"fast_track_{proc.id}",
            content_text=text
        )
        db.add(doc)
        db.commit()

        # 4. Indexa RAG
        index_process(db, proc.office_id, proc.id)

        # 5. Gera Petição Inicial Imediata
        petition = generate_petition_draft(
            db=db,
            office_id=proc.office_id,
            process_id=proc.id,
            mode="attack",
            style="formal",
            notes="Gerado automaticamente via Fast Track (Áudio)."
        )

        return {
            "ok": True,
            "process_id": proc.id,
            "client_name": client_name,
            "petition": petition.get("draft") if petition.get("ok") else None,
            "transcription": text
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/transcribe")
def transcribe_meeting(
    file: UploadFile = File(...),
    process_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recebe um arquivo de áudio, transcreve com Whisper e salva como Documento do processo.
    Após salvar, atualiza o índice RAG do processo.
    """
    proc = (
        db.query(Process)
        .filter(
            Process.id == process_id,
            Process.office_id == current_user.office_id,
        )
        .first()
    )
    if not proc:
        raise HTTPException(status_code=404, detail="Processo não encontrado ou sem permissão.")

    # Cria arquivo temporário para o áudio
    fd, temp_path = tempfile.mkstemp(suffix=".webm") 
    os.close(fd)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Chama Whisper
        transcription_text = transcribe_audio(temp_path)
        
        if not transcription_text:
            raise HTTPException(status_code=500, detail="A transcrição falhou ou retornou vazia.")

        # Salva o texto como um Documento
        doc = Document(
            office_id=proc.office_id,
            process_id=proc.id,
            category="Transcrição de Reunião",
            status="uploaded",
            file_name=f"transcricao_{file.filename}.txt",
            mime_type="text/plain",
            drive_file_id=f"audio_trans_mock_{proc.id}",
            content_text=transcription_text
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Opcionalmente re-indexa agora o processo para o RAG
        index_process(db, proc.office_id, proc.id)
        
        return {
            "ok": True,
            "message": "Áudio transcrito e salvo no processo com sucesso.",
            "transcription": transcription_text,
            "document_id": doc.id
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
