from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SendEmailRequest(BaseModel):
    process_id: int = Field(..., gt=0)
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)

class EmailLogResponse(BaseModel):
    id: int
    process_id: Optional[int]
    client_id: Optional[int]
    to_email: str
    subject: str
    status: str
    error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
