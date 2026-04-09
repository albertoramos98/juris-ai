
import os
import json
from app.core.database import SessionLocal
from app.services.rag_service import compose_process

def test_fix():
    db = SessionLocal()
    # Testando com o Processo 55 (Alberto Ramos) do Office 2
    print("Iniciando teste de geração para Processo 55 (Alberto Ramos)...")
    
    result = compose_process(
        db=db,
        office_id=2,
        process_id=55,
        mode="attack",
        style="formal"
    )
    
    db.close()
    
    if not result.get("ok"):
        print(f"ERRO NO TESTE: {result.get('detail')}")
        return

    comp = result.get("composition", {})
    full_text = comp.get("full_text", "").lower()
    
    print("\n--- RESULTADO DO TESTE ---")
    if "elton" in full_text:
        print("FALHA: O nome 'Elton' ainda apareceu no texto!")
    else:
        print("SUCESSO: Nome 'Elton' NÃO localizado no texto.")
        
    if "alberto" in full_text:
        print("SUCESSO: Nome do cliente real 'Alberto Ramos' identificado no texto!")
    else:
        print("AVISO: Nome 'Alberto' não apareceu explicitamente, mas o Elton foi ignorado.")

    print("\nTrecho inicial do texto gerado:")
    print(comp.get("full_text", "")[:300] + "...")

if __name__ == "__main__":
    test_fix()
