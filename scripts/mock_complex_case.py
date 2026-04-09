from sqlalchemy import create_engine, text
from datetime import date, datetime, timedelta

engine = create_engine("sqlite:///dev.db")

ALBERTO_OFFICE_ID = 2

def run():
    with engine.connect() as conn:
        # 1. Cria Cliente
        client_name = "Construtora Alpha S.A."
        conn.execute(text("""
            INSERT INTO clients (name, document, email, office_id)
            VALUES (:name, :document, :email, :office_id)
        """), {
            "name": client_name,
            "document": "12.345.678/0001-99",
            "email": "juridico@construtoraalpha.com.br",
            "office_id": ALBERTO_OFFICE_ID
        })
        client_id = conn.execute(text("SELECT last_insert_rowid()")).scalar()
        
        # 2. Cria Processo Complexo
        process_number = "0001234-56.2024.8.19.0001"
        conn.execute(text("""
            INSERT INTO processes (number, court, type, status, client_id, office_id, rag_chunk_count)
            VALUES (:number, :court, :type, :status, :client_id, :office_id, :rag_chunk_count)
        """), {
            "number": process_number,
            "court": "5ª Vara Cível da Comarca da Capital",
            "type": "Ação de Rescisão Contratual c/c Indenização",
            "status": "ativo",
            "client_id": client_id,
            "office_id": ALBERTO_OFFICE_ID,
            "rag_chunk_count": 150
        })
        process_id = conn.execute(text("SELECT last_insert_rowid()")).scalar()
        
        # 3. Cria Prazos
        deadlines = [
            {"description": "Protocolar Contestação", "due_date": (date.today() + timedelta(days=5)).isoformat(), "responsible": "Dr. Alberto", "is_critical": 1, "process_id": process_id, "office_id": ALBERTO_OFFICE_ID, "status": "pending", "completed": 0},
            {"description": "Juntar Procuração e Custas", "due_date": (date.today() + timedelta(days=2)).isoformat(), "responsible": "Secretaria", "is_critical": 0, "process_id": process_id, "office_id": ALBERTO_OFFICE_ID, "status": "pending", "completed": 0}
        ]
        for d in deadlines:
            conn.execute(text("INSERT INTO deadlines (description, due_date, responsible, is_critical, process_id, office_id, status, completed) VALUES (:description, :due_date, :responsible, :is_critical, :process_id, :office_id, :status, :completed)"), d)
            
        # 4. Cria Eventos
        conn.execute(text("INSERT INTO process_events (office_id, process_id, type, title, description, created_at) VALUES (:off, :pid, 'process_created', 'Abertura', 'Processo Mockado', :now)"), 
                     {"off": ALBERTO_OFFICE_ID, "pid": process_id, "now": datetime.now().isoformat()})
            
        conn.commit()
        print(f"Mock restaurado: Construtora Alpha")

if __name__ == "__main__":
    run()
