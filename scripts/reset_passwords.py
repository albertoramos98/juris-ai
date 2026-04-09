from app.core.database import SessionLocal
from app.models.user import User
from app.auth.service import get_password_hash

db = SessionLocal()

users = db.query(User).all()

for user in users:
    user.password = get_password_hash("123456")

db.commit()
db.close()

print("✅ Senhas resetadas com sucesso")
