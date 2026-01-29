from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.permissions.dependencies import ensure_office_not_blocked

from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientResponse

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("/", response_model=ClientResponse)
def create_client(
    data: ClientCreate,
    db: Session = Depends(get_db),  
    user: User = Depends(ensure_office_not_blocked),
):
    client = Client(
    name=data.name,
    document=data.document,
    email=data.email,
    office_id=user.office_id,
)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/", response_model=list[ClientResponse])
def list_clients(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Client)
        .filter(Client.office_id == user.office_id)
        .all()
    )
