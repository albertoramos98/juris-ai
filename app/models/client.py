from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)     # EMAIL 👈
    document = Column(String, nullable=True)  # CPF/CNPJ
    office_id = Column(Integer, ForeignKey("offices.id"), nullable=False)
