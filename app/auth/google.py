from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.settings import settings
from app.models.user import User
from app.models.office import Office  # ajuste se necessário
from app.models.google_token import GoogleToken  # <<< ADD

router = APIRouter(prefix="/auth/google", tags=["Auth - Google"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/calendar",
     "https://www.googleapis.com/auth/drive.file"
]


# ======================
# helpers: state + jwt
# ======================
def _make_state() -> str:
    payload = {
        "nonce": token_urlsafe(16),
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _decode_state(state: str) -> dict:
    return jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def _create_access_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": email, "exp": int(expire.timestamp())}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@router.get("/login")
def google_login():
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured in .env")

    state = _make_state()

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",            # <<< precisa pra refresh token
        "include_granted_scopes": "true",
        "prompt": "consent",                 # <<< força refresh token na primeira vez
        "state": state,
    }

    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/callback")
def google_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    # 1) valida state (anti-CSRF)
    try:
        _decode_state(state)
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid state")

    # 2) troca code por tokens
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }

    resp = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=15)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {resp.text}")

    token_data = resp.json()

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")  # pode vir None dependendo do consent
    token_type = token_data.get("token_type")
    scope = token_data.get("scope")
    expires_in = token_data.get("expires_in")

    if not access_token:
        raise HTTPException(status_code=400, detail="No access_token returned by Google")

    expires_at = None
    if expires_in:
        try:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        except Exception:
            expires_at = None

    # 3) pega email do Google via userinfo
    u = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    if u.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Failed to fetch userinfo: {u.text}")

    info = u.json()
    email = (info.get("email") or "").strip().lower()
    email_verified = bool(info.get("email_verified"))

    if not email or not email_verified:
        raise HTTPException(status_code=400, detail="Google email not verified or missing")

    # 4) garante office da demo (multi-user no mesmo escritório)
    office = db.query(Office).first()
    if not office:
        office = Office(name="Office Demo")
        db.add(office)
        db.commit()
        db.refresh(office)

    # 5) regra de owner (MVP): primeiro usuário do office vira owner
    existing_owner = (
        db.query(User.id)
        .filter(User.office_id == office.id, User.is_owner.is_(True))
        .first()
    )
    make_owner = existing_owner is None

    # 6) cria/acha usuário no Juris
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            password=token_urlsafe(32),  # placeholder
            office_id=office.id,
            is_owner=make_owner,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if make_owner and not user.is_owner:
            user.is_owner = True
            db.add(user)
            db.commit()
            db.refresh(user)

    # 7) salva/atualiza GoogleToken por office (drive/calendar)
    now = datetime.now(timezone.utc)

    gt = db.query(GoogleToken).filter(GoogleToken.office_id == office.id).first()
    if not gt:
        gt = GoogleToken(
            office_id=office.id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            scope=scope,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
        )
        db.add(gt)
    else:
        gt.access_token = access_token
        # não perde refresh_token antigo se o google não mandar um novo
        if refresh_token:
            gt.refresh_token = refresh_token
        gt.token_type = token_type
        gt.scope = scope
        gt.expires_at = expires_at
        gt.updated_at = now
        db.add(gt)

    db.commit()

    # 8) emite token do Juris e manda pro front
    juris_token = _create_access_token(email)
    redirect_to = f"{settings.FRONTEND_LOGIN_REDIRECT}?token={juris_token}"
    return RedirectResponse(redirect_to)
