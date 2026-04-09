from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


class ProcessEvent(Base):
    __tablename__ = "process_events"

    id = Column(Integer, primary_key=True, index=True)

    office_id = Column(Integer, ForeignKey("offices.id"), nullable=False, index=True)
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=False, index=True)

    # ex: "deadline_created", "doc_uploaded", "email_flow_started"
    type = Column(String(64), nullable=False, index=True)

    # texto curtinho pra UI
    title = Column(String(160), nullable=False)

    # texto mais humano/detalhado
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_now, index=True)

    # (opcional) relações pra facilitar queries
    process = relationship("Process", backref="events")

    __table_args__ = (
        Index("ix_process_events_office_process_created", "office_id", "process_id", "created_at"),
    )
