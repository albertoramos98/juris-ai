from pydantic import BaseModel, EmailStr, Field


class OfficeUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    is_owner: bool = False  # opcional (por padrão: membro)


class OfficeUserOut(BaseModel):
    id: int
    email: EmailStr
    office_id: int
    is_owner: bool

    class Config:
        from_attributes = True
