
from app.core.database import SessionLocal
from app.models.process import Process
from app.models.document_chunk import DocumentChunk
from app.models.chunk_embedding import ChunkEmbedding
from app.services.rag_service import index_process

def clean_and_reindex():
    db = SessionLocal()
    office_id = 2
    
    print(f"Limpando dados antigos do Office {office_id}...")
    db.query(ChunkEmbedding).filter(ChunkEmbedding.office_id == office_id).delete()
    db.query(DocumentChunk).filter(DocumentChunk.office_id == office_id).delete()
    db.commit()
    
    processes = db.query(Process).filter(Process.office_id == office_id).all()
    print(f"Encontrados {len(processes)} processos para re-indexar.")
    
    for p in processes:
        print(f"Indexando processo {p.number} (ID: {p.id})...")
        res = index_process(db, office_id, p.id)
        print(f"Resultado: {res}")
        
    db.close()

if __name__ == "__main__":
    clean_and_reindex()
