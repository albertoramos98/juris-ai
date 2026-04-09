from __future__ import annotations

import os
import json
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.services.document_extractor import extract_text

router = APIRouter(prefix="/styles", tags=["styles"])

STYLE_GUIDE_PATH = "office_style_guide.json"

def analyze_style(text):
    if not text: return {}
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    # Pega os primeiros blocos significativos para o cabeçalho
    header = "\n".join(lines[:15])
    # Pega o final para o fecho
    footer = "\n".join(lines[-15:])
    # Tópicos em caixa alta
    topics = [l for l in lines if l.isupper() and 3 < len(l) < 60]
    return {
        "header": header,
        "footer": footer,
        "common_topics": list(set(topics))[:15]
    }

@router.post("/train")
async def train_style(
    category: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Analisa um documento (PDF, DOCX, TXT) para extrair o estilo visual 
    (cabeçalho, fecho, tópicos) e salvar no guia do escritório.
    """
    allowed_extensions = ['.docx', '.pdf', '.txt']
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=400, detail="Formato não suportado. Use .docx, .pdf ou .txt")

    try:
        content = await file.read()
        text = extract_text(content, file.filename or "")
        
        if not text or len(text) < 50:
            raise HTTPException(status_code=400, detail="Documento muito curto ou sem texto extraível.")

        new_style = analyze_style(text)
        new_style["filename"] = file.filename

        # Carrega guia atual
        guide = {}
        if os.path.exists(STYLE_GUIDE_PATH):
            try:
                with open(STYLE_GUIDE_PATH, "r", encoding="utf-8") as f:
                    guide = json.load(f)
            except Exception:
                guide = {}

        # Atualiza a categoria (mantendo apenas o mais recente ou uma lista)
        if category not in guide:
            guide[category] = []
        
        # Adiciona ao início da lista para ser o "padrão"
        guide[category].insert(0, new_style)
        guide[category] = guide[category][:5] # Mantém os 5 últimos

        with open(STYLE_GUIDE_PATH, "w", encoding="utf-8") as f:
            json.dump(guide, f, indent=4, ensure_ascii=False)

        return {"ok": True, "message": f"Estilo de {category} atualizado com sucesso!", "style": new_style}

    except Exception as e:
        print(f"Erro no treinamento de estilo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/current")
async def get_current_styles(current_user: User = Depends(get_current_user)):
    if os.path.exists(STYLE_GUIDE_PATH):
        try:
            with open(STYLE_GUIDE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}
