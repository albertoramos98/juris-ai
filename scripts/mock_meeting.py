
import json
from datetime import datetime
from app.core.database import SessionLocal
from app.models.document import Document
from app.models.process_event import ProcessEvent
from app.services.rag_service import index_process

def mock_meeting_transcription():
    db = SessionLocal()
    process_id = 55 # Alberto Ramos
    office_id = 2
    
    meeting_text = """
    TRANSCRIÇÃO DA REUNIÃO - 31/03/2026
    Participantes: Advogado Master e Cliente Alberto Ramos.
    
    Pontos Decididos:
    1. O cliente Alberto Ramos autorizou a entrada da Reclamação Trabalhista contra a empresa 'Logística S.A.'.
    2. Ficou combinado que os honorários advocatícios serão de 25% sobre o êxito da causa.
    3. O Alberto mencionou que trabalhou na empresa por 5 anos sem receber horas extras, entrando às 07:00 e saindo às 19:00.
    4. Ele prometeu enviar as fotos dos cartões de ponto pelo WhatsApp até amanhã cedo.
    5. A reunião foi encerrada com o compromisso de protocolar a inicial na próxima sexta-feira.
    """
    
    print(f"Criando transcrição fake para o Processo {process_id}...")
    
    # 1. Cria o documento
    doc = Document(
        office_id=office_id,
        process_id=process_id,
        category="Transcrição de Reunião",
        status="uploaded",
        file_name="reuniao_estrategica_31_03.txt",
        mime_type="text/plain",
        drive_file_id="mock_audio_12345",
        content_text=meeting_text,
        created_at=datetime.utcnow()
    )
    db.add(doc)
    
    # 2. Registra o evento na Timeline
    event = ProcessEvent(
        office_id=office_id,
        process_id=process_id,
        type="document_uploaded",
        title="Transcrição de Áudio Gerada",
        description="Reunião estratégica com Alberto Ramos transcrita via IA.",
        created_at=datetime.utcnow()
    )
    db.add(event)
    
    db.commit()
    db.refresh(doc)
    
    print(f"Documento ID {doc.id} criado. Iniciando Re-indexação RAG...")
    
    # 3. Re-indexa o processo para a IA aprender
    index_res = index_process(db, office_id, process_id)
    
    db.close()
    print(f"Sucesso! Resultado da indexação: {index_res}")
    print("\n--- TESTE PRONTO ---")
    print("Agora você pode ir no chat da IA e perguntar: 'Quais foram os 5 pontos decididos na reunião com o Alberto?'")

if __name__ == "__main__":
    mock_meeting_transcription()
