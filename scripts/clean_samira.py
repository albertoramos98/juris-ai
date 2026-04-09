from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///dev.db")

PROCESS_ID = 56

with engine.connect() as conn:
    # 1. Limpa o content_text de arquivos que não deveriam ter texto (imagens, áudio)
    # ou que estão com lixo binário.
    # No SQLite, vamos usar extensões comuns pra identificar.
    query = text("""
        UPDATE documents 
        SET content_text = NULL 
        WHERE process_id = :pid 
          AND (
            file_name LIKE '%.png' OR 
            file_name LIKE '%.jpg' OR 
            file_name LIKE '%.jpeg' OR 
            file_name LIKE '%.wav' OR 
            file_name LIKE '%.mp3' OR 
            file_name LIKE '%.mp4'
          )
    """)
    conn.execute(query, {"pid": PROCESS_ID})
    
    # 2. Opcional: Limpa TUDO do Samira pra forçar re-indexação limpa
    # conn.execute(text("UPDATE documents SET content_text = NULL WHERE process_id = :pid"), {"pid": PROCESS_ID})
    
    # 3. Remove chunks antigos desse processo
    conn.execute(text("DELETE FROM document_chunks WHERE process_id = :pid"), {"pid": PROCESS_ID})
    conn.execute(text("DELETE FROM chunk_embeddings WHERE process_id = :pid"), {"pid": PROCESS_ID})
    
    # 4. Reseta flags no processo
    conn.execute(text("UPDATE processes SET rag_indexed_at = NULL, rag_chunk_count = 0 WHERE id = :pid"), {"pid": PROCESS_ID})
    
    conn.commit()
    print(f"Limpeza do processo {PROCESS_ID} (Samira) concluída.")
