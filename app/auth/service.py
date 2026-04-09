from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
import bcrypt

from app.core.settings import settings
from app.models.user import User

# Adicionado bcrypt para suporte total aos hashes do banco
pwd_context = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"],
    deprecated="auto"
)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        # Tenta via passlib (que gerencia múltiplos esquemas)
        return pwd_context.verify(plain, hashed)
    except Exception:
        # Fallback manual para bcrypt caso o passlib falhe por erro de versão/formato
        try:
            return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
        except:
            return False


def authenticate_user(db, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
