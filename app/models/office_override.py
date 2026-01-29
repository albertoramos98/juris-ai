from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, func
from app.core.database import Base


class OfficeOverride(Base):
    __tablename__ = "office_overrides"

    id = Column(Integer, primary_key=True, index=True)

    office_id = Column(Integer, ForeignKey("offices.id"), nullable=False, index=True)
    unlocked_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    reason = Column(String, nullable=True)

    # Melhor pra DB: o banco grava o "agora" (evita drift)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # O "expires_at" você define no backend quando cria o override
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
