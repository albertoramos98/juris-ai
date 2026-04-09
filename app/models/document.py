from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Text
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    office_id = Column(Integer, ForeignKey("offices.id"), nullable=False, index=True)
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=False, index=True)

    category = Column(String, nullable=False)
    status = Column(String, nullable=False, default="uploaded")

    file_name = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)

    drive_file_id = Column(String, nullable=False, index=True)
    drive_web_view_link = Column(String, nullable=True)

    # 🧠 NOVO — texto extraído para IA/RAG
    content_text = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
