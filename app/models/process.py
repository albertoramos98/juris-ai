from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base

class Process(Base):
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, nullable=False, index=True)
    court = Column(String, nullable=False)  # Vara
    type = Column(String, nullable=False)   # Tipo de ação
    status = Column(String, default="ativo")

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    office_id = Column(Integer, ForeignKey("offices.id"), nullable=False)
