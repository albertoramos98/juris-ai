from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.core.database import Base

class EmailFlow(Base):
    __tablename__ = "email_flows"

    id = Column(Integer, primary_key=True, index=True)

    office_id = Column(Integer, ForeignKey("offices.id"), nullable=False, index=True)
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=False, index=True)

    active = Column(Boolean, default=True, nullable=False)

    interval_days = Column(Integer, default=3, nullable=False)
    max_attempts = Column(Integer, default=10, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)

    last_sent_at = Column(DateTime, nullable=True)

    # opcional: guardar “último template” usado
    template = Column(String, default="cobranca_docs", nullable=False)

    # stop automático quando receber doc (Sprint 1 docs já existe)
    stop_on_any_upload = Column(Boolean, default=True, nullable=False)
    stopped_reason = Column(String, nullable=True)
    stopped_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
