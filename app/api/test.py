from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/test", tags=["test"])

@router.get("/protected")
def protected(user: User = Depends(get_current_user)):
    return {
        "message": "rota protegida",
        "user_id": user.id,
        "office_id": user.office_id
    }
