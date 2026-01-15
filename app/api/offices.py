from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.user_block import UserBlock

router = APIRouter(prefix="/offices", tags=["Offices"])


def _ensure_owner(user: User):
    if not getattr(user, "is_owner", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can perform this action.",
        )


@router.post("/me/users/{user_id}/unlock")
def unlock_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_owner(current_user)

    # (opcional) evita desbloquear alguém de outro office por id aleatório
    target_user = (
        db.query(User)
        .filter(User.id == user_id, User.office_id == current_user.office_id)
        .first()
    )
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found in this office.")

    block = (
        db.query(UserBlock)
        .filter(
            UserBlock.office_id == current_user.office_id,
            UserBlock.user_id == user_id,
            UserBlock.resolved_at.is_(None),
        )
        .order_by(UserBlock.blocked_at.desc())
        .first()
    )

    if not block:
        return {"ok": True, "message": "User is not blocked."}

    block.resolved_at = datetime.now(timezone.utc)
    block.resolved_by = current_user.id
    db.commit()

    return {"ok": True, "message": "User unlocked.", "block_id": block.id}
