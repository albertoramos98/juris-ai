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
    
    # Extrai o texto do PDF
    text = extract_text(content, "application/pdf")
    if not text:
        print("Erro: Nenhum texto extraído.")
        return

    # Quebra em chunks de ~1500 chars para melhor recuperação
    chunks = [text[i:i+1500] for i in range(0, len(text), 1300)]
    print(f"Total de blocos gerados: {len(chunks)}")

    # Processa em lotes de 20 para a API da OpenAI
    batch_size = 20
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        print(f"Vetorizando lote {i//batch_size + 1}...")
        vectors = embed_texts(batch)
        
        for content_chunk, vec in zip(batch, vectors):
            new_gk = GlobalKnowledge(
                office_id=office_id,
                title=f"{os.path.basename(file_path)} - Parte {chunks.index(content_chunk)+1}",
                category=category,
                content_text=content_chunk,
                embedding_json=json.dumps(vec)
            )
            db.add(new_gk)
        db.commit()
    
    print(f"Sucesso: {file_path} indexado.")
    db.close()

# Executa para os dois ebooks
office_id = 1 # Admin Principal
ingest_ebook(r"C:\Users\alber\Desktop\juris-ai sandbox\juris-ai\EBOOK - ILMM 01 (1) (1) (2).pdf", office_id)
# O segundo ebook é muito grande, vou processar os primeiros 100 blocos para o teste não demorar demais
# ingest_ebook(r"C:\Users\alber\Desktop\juris-ai sandbox\juris-ai\Ebook.pdf", office_id)
