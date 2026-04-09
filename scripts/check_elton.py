
from app.core.database import SessionLocal
from app.models.client import Client
from app.models.process import Process
from app.models.global_knowledge import GlobalKnowledge

db = SessionLocal()
print("--- Clientes 'Elton' ---")
clients = db.query(Client).filter(Client.name.like('%Elton%')).all()
for c in clients:
    print(f"ID: {c.id} | Nome: {c.name}")
    procs = db.query(Process).filter(Process.client_id == c.id).all()
    for p in procs:
        print(f"  Processo ID: {p.id} | Chunks: {p.rag_chunk_count}")

print("\n--- Base Global Knowledge (Doutrina/Jurisprudência) ---")
gk = db.query(GlobalKnowledge).filter(GlobalKnowledge.content_text.like('%Elton%')).all()
for g in gk:
    print(f"GK ID: {g.id} | Título: {g.title} | Categoria: {g.category}")
db.close()
