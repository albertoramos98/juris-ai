from pydantic import BaseModel
from typing import Any, Optional, List, Dict

class ImportErrorItem(BaseModel):
    row: int
    field: str
    message: str

class ProcessImportRow(BaseModel):
    number: str
    client_name: str
    court: str
    type: str
    status: Optional[str] = "ativo"

class ImportPreviewResponse(BaseModel):
    columns: List[str]
    sample: List[Dict[str, Any]]
    total_rows: int
    valid_rows: int
    error_rows: int
    errors: List[ImportErrorItem]

class ImportCommitResponse(BaseModel):
    total_rows: int
    created: int
    updated: int
    failed: int
    errors: List[ImportErrorItem]
