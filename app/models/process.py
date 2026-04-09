from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Process(Base):
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, nullable=False, index=True)
    court = Column(String, nullable=False)  # Vara
    type = Column(String, nullable=False)   # Tipo de ação
    status = Column(String, default="ativo")
    drive_folder_id = Column(String, nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    office_id = Column(Integer, ForeignKey("offices.id"), nullable=False)
    rag_indexed_at = Column(DateTime, nullable=True)
    rag_chunk_count = Column(Integer, nullable=False, default=0)

    client = relationship("Client")
    office = relationship("Office")
