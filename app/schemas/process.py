from pydantic import BaseModel

class ProcessCreate(BaseModel):
    number: str
    court: str
    type: str
    client_id: int

class ProcessResponse(BaseModel):
    id: int
    number: str
    court: str
    type: str
    status: str
    client_id: int

    class Config:
        from_attributes = True
