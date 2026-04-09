
import json
import os
from datetime import datetime
from app.core.database import SessionLocal
from app.models.client import Client
from app.models.process import Process
from app.models.document import Document
from app.models.chunk_embedding import ChunkEmbedding
from app.services.openai_service import extract_case_info
from app.services.rag_service import index_process, generate_petition_draft, query_process

def run_fine_grained_test():
    db = SessionLocal()
    office_id = 2 # Nosso escritório de teste
    
    # SIMULAÇÃO DE TRANSCRIÇÃO DE ÁUDIO REAL (MUITO DETALHADA)
    mock_transcription = """
    Olá, doutor. Meu nome é Marcos Vinícius Ferreira. 
    Eu vim aqui hoje porque quero entrar com um processo de Danos Morais contra a operadora de celular 'Conecta Brasil'.
    O que aconteceu foi que eles negativaram meu nome indevidamente no SERASA por uma conta que eu já tinha pago em janeiro de 2026.
    O valor da conta era de 150 reais. Eu tenho o comprovante aqui. 
    Meu nome ficou sujo por 3 meses e eu não consegui financiar minha moto por causa disso. 
    Eu moro aqui no Recife e gostaria que o processo corresse na vara cível daqui.
    """
    
    print("--- INICIANDO TESTE PENTE FINO: FAST TRACK ---")
    
    # 1. Teste de Extração de Info via IA
    print("\n1. Testando Extração de Informações via IA...")
    info = extract_case_info(mock_transcription)
    print(f"Dados extraídos: {info}")
    
    assert "Marcos" in info.get("client_name", ""), "Erro: Nome do cliente não extraído."
    assert "Conecta" in info.get("case_type", "") or "Danos" in info.get("case_type", ""), "Erro: Tipo de ação não extraído."
    
    # 2. Simulação do Fluxo de Banco de Dados
    print("\n2. Simulando Criação Automática no Banco de Dados...")
    client = Client(name=info['client_name'], office_id=office_id, email="", document="")
    db.add(client)
    db.commit()
    db.refresh(client)
    
    proc = Process(
        office_id=office_id,
        client_id=client.id,
        number=f"TEST-{datetime.now().strftime('%Y%m%d%H%M')}",
        court=info.get("court", "Recife"),
        type=info.get("case_type", "Danos Morais"),
        status="ativo"
    )
    db.add(proc)
    db.commit()
    db.refresh(proc)
    print(f"Processo criado ID: {proc.id} para o Cliente: {client.name}")
    
    # 3. Teste de Indexação Automática
    print("\n3. Testando Indexação RAG Automática...")
    doc = Document(
        office_id=office_id,
        process_id=proc.id,
        category="Transcrição de Reunião",
        status="uploaded",
        file_name="test_fast_track.txt",
        mime_type="text/plain",
        drive_file_id="test_123",
        content_text=mock_transcription
    )
    db.add(doc)
    db.commit()
    
    index_res = index_process(db, office_id, proc.id)
    print(f"Resultado da Indexação: {index_res}")
    
    # Verificação física de vetores
    emb_count = db.query(ChunkEmbedding).filter_by(process_id=proc.id).count()
    print(f"Vetores gerados no banco: {emb_count}")
    assert emb_count > 0, "Erro: Nenhum vetor gerado para o áudio."
    
    # 4. Teste de Geração de Petição Imediata
    print("\n4. Testando Geração de Petição Inicial baseada no Áudio...")
    petition = generate_petition_draft(
        db=db,
        office_id=office_id,
        process_id=proc.id,
        mode="attack",
        style="formal",
        notes="Gerado via Fast Track Test."
    )
    
    draft = petition.get("draft", {})
    full_text = draft.get("full_text", "").lower()
    
    print(f"Peticao Gerada (Tamanho): {len(full_text)} caracteres.")
    assert "conecta brasil" in full_text, "Erro: Nome da empresa ré não consta na petição."
    assert "serasa" in full_text, "Erro: Fato principal (SERASA) não consta na petição."
    assert "marcos vinícius" in full_text, "Erro: Nome do autor incorreto na petição."
    print("Sucesso: Petição gerada com os fatos corretos!")
    
    # 5. Teste de Consulta de Chat (RAG)
    print("\n5. Testando Consulta de Chat (RAG)...")
    query_res = query_process(db, office_id, proc.id, "Qual o valor da conta que o Marcos pagou?")
    print(f"Resposta da IA: {query_res.get('answer')}")
    assert "150" in query_res.get('answer', ""), "Erro: IA não localizou o valor no áudio indexado."
    
    print("\n--- TESTE PENTE FINO FINALIZADO COM SUCESSO! ---")
    print("Todas as camadas (Extração, Banco, Indexação e Redação) estão operacionais.")
    
    db.close()

if __name__ == "__main__":
    run_fine_grained_test()
