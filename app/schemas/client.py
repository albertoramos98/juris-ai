from pydantic import BaseModel
from typing import Optional

class ClientCreate(BaseModel):
    name: str
    document: Optional[str] = None
    email: Optional[str] = None

class ClientResponse(BaseModel):
    id: int
    name: str
    document: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True
