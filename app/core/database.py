from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# Ajuste para Supabase/Render/Railway
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Adiciona sslmode=require se for PostgreSQL e não tiver parâmetros
if "postgresql" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    separator = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL += f"{separator}sslmode=require"

# REMOVE pgbouncer=true pois o psycopg2 (Python) não aceita esse parâmetro no DSN
if "pgbouncer=true" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("pgbouncer=true", "")
    DATABASE_URL = DATABASE_URL.replace("&&", "&").replace("?&", "?").rstrip("?").rstrip("&")

connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True # Evita erros de conexão perdida (comum no Supabase/Railway)
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
