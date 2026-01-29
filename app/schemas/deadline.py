from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class DeadlineCreate(BaseModel):
    description: str
    due_date: date
    responsible: str
    process_id: int
    is_critical: bool = False


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
