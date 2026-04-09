from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.service import authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        email=form_data.username,
        password=form_data.password,
    )

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if hasattr(user, "is_active") and not user.is_active:
        raise HTTPException(status_code=423, detail="User inactive")

    token = create_access_token({
        "sub": str(user.id),           # ✅ agora é ID, não email
        "email": user.email,           # opcional, mas ótimo
        "office_id": user.office_id,
        "is_owner": user.is_owner,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
    }