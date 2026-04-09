from sqlalchemy import create_engine, text
from datetime import date, datetime, timedelta

engine = create_engine("sqlite:///dev.db")
ALBERTO_OFFICE_ID = 2

scenarios = [
    {
        "client": {"name": "Tecno Logística Ltda", "doc": "22.333.444/0001-55", "email": "contato@tecnolog.com.br"},
        "process": {"number": "1023456-78.2023.8.26.0100", "court": "Foro Central Cível de São Paulo - TJSP", "type": "Dissolução Parcial de Sociedade", "status": "ativo"}
    },
    {
        "client": {"name": "Indústrias Reunidas do Sul", "doc": "33.444.555/0001-66", "email": "juridico@irsul.com.br"},
        "process": {"number": "0045678-12.2022.4.01.3400", "court": "7ª Vara Federal Cível da SJDF - TRF1", "type": "Anulatória de Débito Fiscal", "status": "ativo"}
    },
    {
        "client": {"name": "Mariana Oliveira da Silva", "doc": "111.222.333-44", "email": "mariana.oliveira@email.com"},
        "process": {"number": "0000987-44.2024.8.17.2001", "court": "12ª Vara Cível da Capital (Recife) - TJPE", "type": "Ação de Despejo por Falta de Pagamento", "status": "ativo"}
    },
    {
        "client": {"name": "Supermercado Horizonte", "doc": "44.555.666/0001-77", "email": "rh@horizonte.com.br"},
        "process": {"number": "0010567-89.2023.5.03.0001", "court": "1ª Vara do Trabalho de Belo Horizonte - TRT3", "type": "Reclamação Trabalhista (Rito Ordinário)", "status": "ativo"}
    }
]

def run():
    with engine.connect() as conn:
        for sc in scenarios:
            conn.execute(text("INSERT INTO clients (name, document, email, office_id) VALUES (:name, :doc, :email, :off)"), 
                         {**sc["client"], "off": ALBERTO_OFFICE_ID})
            client_id = conn.execute(text("SELECT last_insert_rowid()")).scalar()
            
            conn.execute(text("""
                INSERT INTO processes (number, court, type, status, client_id, office_id, rag_chunk_count)
                VALUES (:number, :court, :type, :status, :client_id, :office_id, 100)
            """), {**sc["process"], "client_id": client_id, "office_id": ALBERTO_OFFICE_ID})
            process_id = conn.execute(text("SELECT last_insert_rowid()")).scalar()
            
            conn.execute(text("INSERT INTO process_events (office_id, process_id, type, title, description, created_at) VALUES (:off, :pid, 'process_created', 'Mock', 'Cenário restaurado', :now)"), 
                         {"off": ALBERTO_OFFICE_ID, "pid": process_id, "now": datetime.now().isoformat()})
        conn.commit()
        print("Mock restaurado: 4 Jurisdições")

if __name__ == "__main__":
    run()
