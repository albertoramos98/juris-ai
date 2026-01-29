from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import requests

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.services.google_oauth import get_valid_access_token

router = APIRouter(prefix="/google/drive", tags=["Google - Drive"])

DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"


@router.get("/files")
def drive_list_files(
    page_size: int = 10,
    q: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Lista arquivos do Google Drive (demo):
    - page_size: quantos itens
    - q: query do Drive (opcional), ex: "mimeType='application/pdf'"
    """
    token = get_valid_access_token(db, user.office_id)

    params = {
        "pageSize": max(1, min(int(page_size), 100)),
        "fields": "files(id,name,mimeType,webViewLink,iconLink,modifiedTime,size),nextPageToken",
        "orderBy": "modifiedTime desc",
    }
    if q:
        params["q"] = q

    r = requests.get(
        DRIVE_FILES_URL,
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=15,
    )

    if r.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Drive list failed ({r.status_code}): {r.text}",
        )

    return r.json()
