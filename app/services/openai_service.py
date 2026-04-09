import os
import json as _json
import re as _re
from dotenv import load_dotenv
from openai import OpenAI
from docx import Document as DocxReader

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")

# =========================
# HELPERS
# =========================

def _read_master_template(mode: str) -> str:
    """Lê o texto integral do modelo original."""
    try:
        if mode == "attack":
            path = os.path.join(os.getcwd(), "MODELOS DE INICIAIS", "inicial Elton Claudino x Fruta Nobre.docx")
        else:
            path = os.path.join(os.getcwd(), "MODELOS CONTESTASÇÃO EMPRESA", "ação nb x sandro julio CIVIL.docx")
        
        if not os.path.exists(path): return "Modelo não encontrado."
        
        doc = DocxReader(path)
        # Mantém a quebra de linha original para preservação de estrutura
        return "\n".join([p.text for p in doc.paragraphs])
    except:
        return "Erro ao ler modelo."

# =========================
# TRANSFORMADOR DE MODELO (RÉPLICA PERFEITA)
# =========================

def compose_attack_defense_json(
    *,
    mode: str,
    style: str,
    notes: str,
    context_blocks: list[str],
    client_name: str = "",
) -> dict:
    """
    Não reescreve a peça. 
    Pega o modelo original e substitui APENAS as informações necessárias.
    """
    master_text = _read_master_template(mode)
    case_context = "\n".join(context_blocks)
    
    # 1. IA gera o mapeamento do que trocar
    instructions = (
        "Você é um assistente de edição jurídica.\n"
        "OBJETIVO: Identificar no MODELO fornecido os trechos que pertencem ao cliente antigo e gerar os trechos substitutos para o NOVO CLIENTE.\n\n"
        "REGRAS:\n"
        "1. Identifique o parágrafo da Qualificação do cliente antigo.\n"
        "2. Identifique os parágrafos de FATOS e FUNDAMENTOS que são específicos do caso antigo.\n"
        "3. Gere a nova Qualificação, Fatos e Fundamentos detalhados para o NOVO CLIENTE.\n"
        "4. NÃO mude as teses jurídicas padronizadas ou doutrinas do modelo.\n"
        "5. Retorne um JSON com as substituições: { 'texto_antigo_exato': 'novo_texto_longo' }."
    )

    prompt = (
        f"MODELO ORIGINAL (TEXTO COMPLETO):\n{master_text[:3000]}\n\n"
        f"DADOS DO NOVO CASO (RAG):\n{case_context}\n\n"
        f"NOVO CLIENTE: {client_name}\n"
        "Gere o JSON de substituição para transformar o modelo original no novo caso."
    )

    try:
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        replacements = _json.loads(resp.choices[0].message.content)
        
        # 2. Aplicamos as substituições no texto do modelo
        final_text = master_text
        for old, new in replacements.items():
            if old.strip() and len(old) > 5: # evita trocar palavras soltas por erro
                final_text = final_text.replace(old, new)

        return {
            "summary": f"Réplica gerada para {client_name}",
            "full_text": final_text,
            "replacements": replacements # guarda para o DOCX
        }
    except Exception as e:
        return {"full_text": master_text, "summary": f"Erro na IA: {str(e)}. Mostrando modelo original."}

# =========================
# OUTRAS FUNÇÕES (MAPEAMENTO E COMPATIBILIDADE)
# =========================

def map_and_replace_template(template_text: str, case_context: str, client_name: str, notes: str = "") -> dict:
    """Usado pelo exportador DOCX para garantir a mesma lógica."""
    # Como a lógica agora é centralizada, podemos apenas chamar o compose e extrair o mapeamento
    res = compose_attack_defense_json(mode="attack", style="formal", notes=notes, context_blocks=[case_context], client_name=client_name)
    return res.get("replacements", {})

def generate_petition_json(**kwargs) -> dict:
    return compose_attack_defense_json(**kwargs)

def embed_texts(texts: list[str]) -> list[list[float]]:
    res = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [item.embedding for item in res.data]

def transcribe_audio(file_path: str) -> str:
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
            return getattr(transcript, "text", "")
    except: return ""

def extract_case_info(text: str) -> dict:
    try:
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "system", "content": "Extraia Nome, Ação e Vara em JSON."}, {"role": "user", "content": text}],
            response_format={"type": "json_object"}
        )
        return _json.loads(resp.choices[0].message.content)
    except: return {"client_name": "Novo Cliente"}

def answer_with_sources(question: str, context_blocks: list[str]) -> str:
    context = "\n".join(context_blocks)
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "system", "content": "Advogado sênior."}, {"role": "user", "content": f"Contexto:\n{context}\n\nQ: {question}"}]
    )
    return resp.choices[0].message.content
