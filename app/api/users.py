from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.service import get_password_hash

from app.models.user import User
from app.schemas.user_admin import OfficeUserCreate, OfficeUserOut

router = APIRouter(prefix="/users", tags=["Users"])


def _ensure_owner(user: User):
    if not bool(getattr(user, "is_owner", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can create users.",
        )


@router.post("/", response_model=OfficeUserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: OfficeUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_owner(current_user)

    email = str(payload.email).lower().strip()

    # email é unique=True no model, mas checar antes dá erro mais bonito
    exists = db.query(User).filter(User.email == email).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use.",
        )

    new_user = User(
        email=email,
        password=get_password_hash(payload.password),  # ✅ passlib hash
        office_id=current_user.office_id,              # ✅ mesmo escritório
        is_owner=bool(payload.is_owner),               # opcional
        is_active=True,                                # ✅ novo: ativo por padrão
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/me/team", response_model=list[OfficeUserOut])
def list_team_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Permite que qualquer membro ativo do escritório veja a equipe
    return (
        db.query(User)
        .filter(
            User.office_id == current_user.office_id,
            User.is_active == True,
        )
        .order_by(User.id.asc())
        .all()
    )


@router.get("/", response_model=list[OfficeUserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_owner(current_user)
    return list_team_members(db, current_user)


@router.patch("/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_owner(current_user)

    target = db.query(User).filter(User.id == user_id).first()
    if not target or target.office_id != current_user.office_id:
        raise HTTPException(status_code=404, detail="User not found")

    # não deixar o owner se desativar
    if target.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate yourself.",
        )

    # segurança: não desativar outro owner (pode remover se quiser)
    if bool(getattr(target, "is_owner", False)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate another owner.",
        )

    # idempotente
    if not bool(getattr(target, "is_active", True)):
        return {"ok": True}

    target.is_active = False
    db.commit()
    return {"ok": True}
