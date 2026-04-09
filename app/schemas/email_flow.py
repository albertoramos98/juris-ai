from datetime import datetime
from pydantic import BaseModel, Field


class EmailFlowCreate(BaseModel):
    process_id: int

    active: bool = True
    interval_days: int = Field(default=3, ge=1, le=365)
    max_attempts: int = Field(default=10, ge=1, le=200)

    template: str = Field(default="cobranca_docs", min_length=1, max_length=80)
    stop_on_any_upload: bool = True


class EmailFlowUpdate(BaseModel):
    active: bool | None = None
    interval_days: int | None = Field(default=None, ge=1, le=365)
    max_attempts: int | None = Field(default=None, ge=1, le=200)

    template: str | None = Field(default=None, min_length=1, max_length=80)
    stop_on_any_upload: bool | None = None


class EmailFlowOut(BaseModel):
    id: int
    office_id: int
    process_id: int

    active: bool
    interval_days: int
    max_attempts: int
    attempts: int

    last_sent_at: datetime | None
    template: str
    stop_on_any_upload: bool

    stopped_reason: str | None
    stopped_at: datetime | None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
