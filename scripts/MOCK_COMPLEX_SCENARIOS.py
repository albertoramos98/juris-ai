
import json
import os
from datetime import datetime
from app.core.database import SessionLocal
from app.models.client import Client
from app.models.process import Process
from app.models.document import Document
from app.services.rag_service import index_process, generate_petition_draft

def run_complex_scenarios():
    db = SessionLocal()
    office_id = 2
    
    scenarios = [
        {
            "name": "Investimentos Alpha Ltda (Representada por Dr. Ricardo)",
            "audio": """
            Doutor, precisamos ajuizar uma ação de indenização e notícia-crime contra nosso ex-CFO, Sr. Wanderley Silva. 
            Detectamos uma fraude contábil sistemática que perdurou por 18 meses. Ele utilizava empresas de fachada para emitir notas fiscais frias de consultoria, 
            desviando um total de 1,2 milhão de reais do nosso fundo de reserva. 
            Temos os balancetes auditados que mostram a discrepância entre o fluxo de caixa real e o reportado. 
            Queremos o bloqueio de bens dele e a reparação integral por fraude corporativa.
            """,
            "type": "Ação de Indenização por Fraude Corporativa"
        },
        {
            "name": "Indústria Têxtil Nordeste S.A.",
            "audio": """
            Estamos com um problema contábil-tributário grave. Nossa auditoria interna identificou que pagamos PIS e COFINS a maior nos últimos 5 anos 
            devido a uma classificação errônea de insumos industriais como bens de consumo. 
            O montante a recuperar é de aproximadamente 850 mil reais. 
            Precisamos de uma ação declaratória de repetição de indébito tributário contra a União Federal para reaver esses valores via compensação ou precatório.
            """,
            "type": "Repetição de Indébito Tributário"
        },
        {
            "name": "Escritório de Advocacia Associados",
            "audio": """
            Infelizmente teremos que processar nosso próprio cliente, a Construtora Landmark. 
            Ganhamos uma causa de 10 milhões de reais para eles no mês passado, mas eles se recusam a pagar os honorários contratuais de 15% sobre o êxito, 
            além de não repassarem os honorários de sucumbência que foram depositados na conta deles por erro do tribunal. 
            O contrato de honorários previa o pagamento em 48 horas após o levantamento do alvará, o que já ocorreu há 15 dias.
            """,
            "type": "Execução de Contrato de Honorários Advocatícios"
        },
        {
            "name": "Dra. Helena Souza (Sócia Minoritária)",
            "audio": """
            Quero sair da sociedade da 'Clínica Médica Vida', mas descobri que meus sócios estão fraudando a apuração de haveres. 
            Eles criaram uma conta paralela, um caixa dois, onde recebem pagamentos de convênios particulares que não passam pela contabilidade oficial da empresa. 
            Isso reduziu artificialmente o valor das minhas cotas em quase 40%. 
            Preciso de uma ação de Dissolução Parcial de Sociedade com pedido de perícia contábil judicial forense para rastrear esses ativos ocultos.
            """,
            "type": "Dissolução Parcial de Sociedade e Apuração de Haveres"
        }
    ]

    print(f"--- INICIANDO PROCESSAMENTO DE {len(scenarios)} CENÁRIOS COMPLEXOS ---")

    for i, sc in enumerate(scenarios):
        print(f"\nProcessando Cenário {i+1}: {sc['name']}...")
        
        # 1. Cria Cliente
        client = db.query(Client).filter(Client.name == sc['name'], Client.office_id == office_id).first()
        if not client:
            client = Client(name=sc['name'], office_id=office_id, email=f"contato{i}@empresa.com.br", document=f"000.000.00{i}-00")
            db.add(client)
            db.commit()
            db.refresh(client)

        # 2. Cria Processo
        proc = Process(
            office_id=office_id,
            client_id=client.id,
            number=f"FT-2026-{i+1:03d}",
            court="Justiça Estadual/Federal",
            type=sc['type'],
            status="ativo"
        )
        db.add(proc)
        db.commit()
        db.refresh(proc)

        # 3. Salva Transcrição
        doc = Document(
            office_id=office_id,
            process_id=proc.id,
            category="Transcrição de Reunião Onboarding",
            status="uploaded",
            file_name=f"transcricao_onboarding_{i+1}.txt",
            mime_type="text/plain",
            drive_file_id=f"drive_audio_ft_{i+1}",
            content_text=sc['audio']
        )
        db.add(doc)
        db.commit()

        # 4. Indexa RAG
        index_process(db, office_id, proc.id)

        # 5. Gera Petição Inicial
        print(f"Gerando Petição Inicial para {sc['name']}...")
        petition = generate_petition_draft(
            db=db,
            office_id=office_id,
            process_id=proc.id,
            mode="attack",
            style="formal",
            notes=f"Caso de alta complexidade: {sc['type']}."
        )
        
        if petition.get("ok"):
            print(f"✓ Petição de {len(petition['draft'].get('full_text', ''))} caracteres gerada com sucesso.")
        else:
            print(f"X Erro na geração: {petition.get('detail')}")

    db.close()
    print("\n--- TODOS OS CENÁRIOS FORAM PROCESSADOS E INDEXADOS ---")

if __name__ == "__main__":
    run_complex_scenarios()
