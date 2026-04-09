from sqlalchemy import create_engine, text
from datetime import datetime

engine = create_engine("sqlite:///dev.db")
ALBERTO_OFFICE_ID = 2

def run():
    with engine.connect() as conn:
        # Busca todos os processos do Alberto
        processes = conn.execute(text("SELECT id, type, number FROM processes WHERE office_id = :off"), {"off": ALBERTO_OFFICE_ID}).fetchall()
        
        for p in processes:
            # Verifica se já tem documento pra não duplicar
            existing = conn.execute(text("SELECT id FROM documents WHERE process_id = :pid"), {"pid": p.id}).first()
            if existing:
                continue

            content = f"""
            PETIÇÃO INICIAL - PROCESSO {p.number}
            TIPO DE AÇÃO: {p.type}
            
            DOS FATOS:
            O autor vem por meio desta relatar que houve uma violação contratual grave no dia 10 de janeiro de 2024. 
            As partes envolvidas tentaram resolução amigável sem sucesso. Os documentos anexos provam a veracidade das alegações.
            O dano causado gerou prejuízos de ordem moral e material, quantificados no valor de R$ 50.000,00.
            
            DO DIREITO:
            Baseia-se a presente demanda no Código Civil Brasileiro e na jurisprudência consolidada dos Tribunais Superiores.
            A responsabilidade civil da parte ré é cristalina, dado o nexo de causalidade entre a omissão e o dano sofrido.
            
            DOS PEDIDOS:
            1. A procedência total da ação;
            2. A condenação da ré ao pagamento de indenização;
            3. A produção de todas as provas em direito admitidas.
            """

            conn.execute(text("""
                INSERT INTO documents (office_id, process_id, category, status, file_name, mime_type, drive_file_id, content_text, created_at)
                VALUES (:off, :pid, 'Petição Inicial', 'uploaded', 'peticao_inicial_mock.pdf', 'application/pdf', 'mock_drive_id', :txt, :now)
            """), {
                "off": ALBERTO_OFFICE_ID,
                "pid": p.id,
                "txt": content.strip(),
                "now": datetime.now().isoformat()
            })
            
        conn.commit()
        print(f"Documentos mockados inseridos em {len(processes)} processos.")

if __name__ == "__main__":
    run()
