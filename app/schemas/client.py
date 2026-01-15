from pydantic import BaseModel

class ClientCreate(BaseModel):
    name: str
    document: str | None = None

class ClientResponse(BaseModel):
    id: int
    name: str
    document: str | None

    class Config:
        from_attributes = True
