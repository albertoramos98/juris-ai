from pydantic import BaseModel, model_validator
from typing import Optional, Any
from datetime import datetime

class ProcessCreate(BaseModel):
    number: str
    court: str
    type: str
    client_id: int
    status: Optional[str] = "ativo"

class ProcessResponse(BaseModel):
    id: int
    number: str
    court: str
    type: str
    action_type: Optional[str] = None
    status: str
    client_id: int
    client_name: Optional[str] = None
    office_id: int
    drive_folder_id: Optional[str] = None
    rag_indexed_at: Optional[datetime] = None
    rag_chunk_count: int

    @model_validator(mode="before")
    @classmethod
    def from_orm_to_dict(cls, data: Any) -> Any:
        if hasattr(data, "id"): # Checa se é um objeto ORM
            # Cria um dict com os campos básicos
            # Mas podemos apenas adicionar os campos extras
            setattr(data, "action_type", data.type)
            if hasattr(data, "client") and data.client:
                setattr(data, "client_name", data.client.name)
            else:
                setattr(data, "client_name", "Cliente não encontrado")
        return data

    class Config:
        from_attributes = True
