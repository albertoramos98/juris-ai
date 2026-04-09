import io

def extract_text(file_bytes: bytes, mime_type: str | None) -> str:
    if not file_bytes:
        return ""

    mt = (mime_type or "").lower()

    try:
        # PDF
        if "pdf" in mt:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            parts = []
            for page in reader.pages:
                parts.append(page.extract_text() or "")
            return "\n".join(parts).strip()

        # DOCX
        if "docx" in mt or "word" in mt:
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs).strip()

        # TXT / plaintext
        if "text/" in mt or mt == "":
            return file_bytes.decode("utf-8", errors="ignore").strip()
            
    except Exception as e:
        print(f"Erro ao extrair texto do arquivo (mime={mt}): {e}")
        return ""

    # Ignora binários não suportados (PNG, WAV, etc)
    return ""
