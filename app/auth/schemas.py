from pydantic import BaseModel, EmailStr

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    office_name: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str
