from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    office_id = Column(Integer, ForeignKey("offices.id"), nullable=False, index=True)

    # governança
    is_owner = Column(Boolean, default=False, nullable=False)

    # acesso (soft delete)
    is_active = Column(Boolean, default=True, nullable=False)

    office = relationship("Office", back_populates="users")
