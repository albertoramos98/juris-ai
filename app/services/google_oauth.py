from __future__ import annotations

from datetime import datetime, timedelta, timezone
import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.google_token import GoogleToken

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def _as_utc_aware(dt: datetime | None) -> datetime | None:
    """
    SQLite costuma voltar datetime naive (sem tzinfo).
    Normaliza para UTC aware.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _is_expired(expires_at: datetime | None) -> bool:
    if not expires_at:
        # se não tem expiração registrada, assume expirado pra forçar refresh
        return True

    expires_at = _as_utc_aware(expires_at)
    now = datetime.now(timezone.utc)

    # margem de 60s
    return expires_at <= (now + timedelta(seconds=60))


def get_valid_access_token(db: Session, office_id: int) -> str:
    gt = db.query(GoogleToken).filter(GoogleToken.office_id == office_id).first()
    if not gt:
        raise HTTPException(
            status_code=400,
            detail="Google not connected for this office. Faça login com Google primeiro.",
        )

    # se token atual ainda é válido, usa ele
    if gt.access_token and not _is_expired(gt.expires_at):
        return gt.access_token

    # se não tem refresh_token, não tem o que fazer
    if not gt.refresh_token:
        raise HTTPException(
            status_code=400,
            detail="No refresh_token saved. Refaça o login do Google com access_type=offline + prompt=consent.",
        )

    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": gt.refresh_token,
        "grant_type": "refresh_token",
    }

    resp = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Token refresh failed: {resp.text}")

    token_data = resp.json()
    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in")  # segundos

    if not access_token:
        raise HTTPException(status_code=400, detail="Refresh did not return access_token.")

    gt.access_token = access_token

    if expires_in:
        gt.expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
    else:
        # se não vier expires_in, força expirar logo
        gt.expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    gt.updated_at = datetime.now(timezone.utc)

    db.add(gt)
    db.commit()
    db.refresh(gt)

    return gt.access_token
