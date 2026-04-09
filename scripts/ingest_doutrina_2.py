import os
import json
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.global_knowledge import GlobalKnowledge
from app.services.document_extractor import extract_text
from app.services.openai_service import embed_texts

def ingest_ebook(file_path, office_id, category="doutrina"):
    db = SessionLocal()
    print(f"Lendo: {file_path}")
    
    with open(file_path, "rb") as f:
        content = f.read()
    
    text = extract_text(content, "application/pdf")
    if not text:
        print("Erro: Nenhum texto extraído.")
        return

    # Para o ebook gigante, vou pegar os primeiros 150.000 caracteres (equivalente a ~100 chunks)
    # Isso cobre uma vasta gama de tópicos iniciais e evita travamentos por tamanho.
    text_sample = text[:150000]
    chunks = [text_sample[i:i+1500] for i in range(0, len(text_sample), 1300)]
    print(f"Total de blocos para indexar (Sample): {len(chunks)}")

    batch_size = 20
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        print(f"Vetorizando lote {i//batch_size + 1}...")
        vectors = embed_texts(batch)
        
        for content_chunk, vec in zip(batch, vectors):
            new_gk = GlobalKnowledge(
                office_id=office_id,
                title=f"Ebook Doutrina - Parte {chunks.index(content_chunk)+1}",
                category=category,
                content_text=content_chunk,
                embedding_json=json.dumps(vec)
            )
            db.add(new_gk)
        db.commit()
    
    print(f"Sucesso: {file_path} (parte estratégica) indexado.")
    db.close()

office_id = 1
ingest_ebook(r"C:\Users\alber\Desktop\juris-ai sandbox\juris-ai\Ebook.pdf", office_id)
