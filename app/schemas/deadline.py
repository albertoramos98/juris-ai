from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class DeadlineCreate(BaseModel):
    description: str
    due_date: date          # <--- aqui
    responsible: str
    is_critical: bool = False
    process_id: int


class DeadlineResponse(BaseModel):
    id: int
    description: str
    due_date: date
    responsible: str

    is_critical: bool
    completed: bool
    status: str

    completed_at: Optional[datetime] = None
    completed_by: Optional[int] = None

    process_id: int

    class Config:
        from_attributes = True
