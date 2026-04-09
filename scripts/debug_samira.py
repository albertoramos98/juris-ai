from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///dev.db")

with engine.connect() as conn:
    # Busca por Samira Davys
    query = text("""
        SELECT p.id, p.number, c.name, p.office_id 
        FROM processes p 
        JOIN clients c ON p.client_id = c.id 
        WHERE c.name LIKE '%Samira%' 
           OR c.name LIKE '%Davys%'
    """)
    results = conn.execute(query).fetchall()
    
    print("--- RESULTADOS DA BUSCA ---")
    for r in results:
        print(f"ID: {r.id} | Número: {r.number} | Cliente: {r.name} | Office: {r.office_id}")
        
        # Busca documentos desse processo
        docs = conn.execute(text("SELECT id, file_name, content_text FROM documents WHERE process_id = :pid"), {"pid": r.id}).fetchall()
        print(f"  Documentos ({len(docs)}):")
        for d in docs:
            txt_size = len(d.content_text) if d.content_text else 0
            print(f"    - [{d.id}] {d.file_name} (Texto extraído: {txt_size} caracteres)")
