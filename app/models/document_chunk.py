from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, func
from app.core.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)

    office_id = Column(Integer, ForeignKey("offices.id"), nullable=False, index=True)
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)

    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
