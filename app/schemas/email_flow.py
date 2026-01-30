from pydantic import BaseModel, Field


class EmailFlowStart(BaseModel):
    process_id: int

    interval_days: int = Field(default=3, ge=1, le=60)
    max_attempts: int = Field(default=10, ge=1, le=200)

    template: str = "cobranca_docs"
    stop_on_any_upload: bool = True


class EmailFlowResponse(BaseModel):
    id: int
    process_id: int
    active: bool

    interval_days: int
    max_attempts: int
    attempts: int

    last_sent_at: str | None = None

    template: str
    stop_on_any_upload: bool

    stopped_reason: str | None = None
    stopped_at: str | None = None

    class Config:
        from_attributes = True
