from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DocumentOut(BaseModel):
    id: int
    office_id: int
    process_id: int
    category: str
    status: str
    file_name: str
    mime_type: Optional[str] = None
    drive_file_id: str
    drive_web_view_link: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
