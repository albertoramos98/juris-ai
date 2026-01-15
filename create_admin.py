from app.core.database import SessionLocal
from app.models.user import User
from app.auth.service import get_password_hash

db = SessionLocal()

user = User(
    email="admin@jurisai.com",
    password=get_password_hash("123456")
)

db.add(user)
db.commit()
db.close()

print("Admin criado com sucesso")
