from sqlalchemy import Column, Integer, ForeignKey, Text, String, DateTime, func
from app.core.database import Base


class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"

    id = Column(Integer, primary_key=True, index=True)

    office_id = Column(Integer, ForeignKey("offices.id"), nullable=False, index=True)
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=False, index=True)

    model = Column(String, nullable=False, default="text-embedding-3-small")
    embedding_json = Column(Text, nullable=False)  # JSON string list[float]

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
