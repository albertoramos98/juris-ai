import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.global_knowledge import GlobalKnowledge
from app.services.openai_service import embed_texts

router = APIRouter(prefix="/global-knowledge", tags=["global_knowledge"])

class KnowledgeCreate(BaseModel):
    title: str
    category: str
    content_text: str

@router.post("/")
def create_knowledge(
    item: KnowledgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Adiciona um novo texto à base fria do escritório (jurisprudência, leis)
    e gera o embedding para busca RAG global.
    """
    try:
        # Gera o embedding usando OpenAI
        vectors = embed_texts([item.content_text])
        if not vectors or not vectors[0]:
            raise HTTPException(status_code=500, detail="Erro ao gerar embedding do texto.")
        
        vec_json = json.dumps(vectors[0])

        new_knowledge = GlobalKnowledge(
            office_id=current_user.office_id,
            title=item.title,
            category=item.category,
            content_text=item.content_text,
            embedding_json=vec_json
        )

        db.add(new_knowledge)
        db.commit()
        db.refresh(new_knowledge)

        return {"ok": True, "message": "Conhecimento global adicionado com sucesso.", "id": new_knowledge.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def list_knowledge(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lista todos os conhecimentos globais do escritório.
    """
    items = db.query(GlobalKnowledge).filter(GlobalKnowledge.office_id == current_user.office_id).all()
    return [{
        "id": item.id,
        "title": item.title,
        "category": item.category,
        "created_at": item.created_at
    } for item in items]
