from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class GlobalKnowledge(Base):
    """
    Armazena a "Base Fria" (Doutrina, Leis, Súmulas, Jurisprudência) do escritório.
    Esses textos são vetorizados (embedding_json) e consultados pelo RAG 
    para fundamentar teses independentemente do processo.
    """
    __tablename__ = "global_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    office_id = Column(Integer, ForeignKey("offices.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String(255), nullable=False) # Ex: "Súmula 331 do TST"
    category = Column(String(50), nullable=True) # Ex: "jurisprudencia", "lei", "tese_interna"
    content_text = Column(Text, nullable=False) # O texto completo da lei/decisão
    
    embedding_json = Column(Text, nullable=True) # O vetor gerado pela OpenAI (para busca rápida)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
