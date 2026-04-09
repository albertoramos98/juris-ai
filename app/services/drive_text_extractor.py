import io
import requests
from typing import Optional, Tuple

from pypdf import PdfReader
from docx import Document as DocxDocument


def _download_drive_file(access_token: str, drive_file_id: str) -> Tuple[bytes, str]:
    """
    Baixa o arquivo do Drive (binário) via files/{fileId}?alt=media.
    Retorna (bytes, content_type_resposta).
    """
    url = f"https://www.googleapis.com/drive/v3/files/{drive_file_id}?alt=media"
    r = requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, timeout=60)
    r.raise_for_status()
    return r.content, (r.headers.get("Content-Type") or "")


def _export_google_doc(access_token: str, drive_file_id: str, export_mime: str) -> bytes:
    """
    Exporta Google Docs/Sheets/Slides via files/{fileId}/export?mimeType=...
    """
    url = f"https://www.googleapis.com/drive/v3/files/{drive_file_id}/export"
    r = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        params={"mimeType": export_mime},
        timeout=60,
    )
    r.raise_for_status()
    return r.content


def _extract_text_from_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    return "\n".join(parts).strip()


def _extract_text_from_docx(data: bytes) -> str:
    doc = DocxDocument(io.BytesIO(data))
    parts = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(parts).strip()


def _extract_text_from_txt(data: bytes) -> str:
    # tenta utf-8, cai pra latin-1
    try:
        return data.decode("utf-8", errors="ignore").strip()
    except Exception:
        return data.decode("latin-1", errors="ignore").strip()


def extract_text_from_drive_file(
    access_token: str,
    drive_file_id: str,
    mime_type: Optional[str],
) -> str:
    """
    Extrai texto de:
    - PDF
    - DOCX
    - TXT
    - Google Docs (exporta pra text/plain)
    - (opcional) Google Drive nativo: tenta export quando for mime do Google
    """
    mt = (mime_type or "").lower().strip()

    # Google Docs nativo ou Word antigo (.doc)
    if mt.startswith("application/vnd.google-apps.") or mt == "application/msword":
        # Google Docs/Sheets/Slides ou Word antigo: exportar texto puro
        try:
            data = _export_google_doc(access_token, drive_file_id, "text/plain")
            return _extract_text_from_txt(data)
        except Exception as e:
            print(f"Erro ao exportar doc/google-app {drive_file_id}: {e}")
            # continua para tentativa de download comum se export falhar
            pass

    # Arquivos “normais”
    data, resp_ct = _download_drive_file(access_token, drive_file_id)
    ct = (resp_ct or "").lower()

    # Preferência: mime_type do banco, mas se estiver vazio usamos Content-Type da resposta
    effective = mt or ct

    if "pdf" in effective:
        return _extract_text_from_pdf(data)

    # DOCX (às vezes vem como application/vnd.openxmlformats-officedocument.wordprocessingml.document)
    if "officedocument.wordprocessingml.document" in effective or effective.endswith("docx"):
        return _extract_text_from_docx(data)

    # Texto simples
    if effective.startswith("text/") or "plain" in effective or effective.endswith("txt"):
        return _extract_text_from_txt(data)

    # fallback: tenta como txt (às vezes o CT vem genérico)
    return _extract_text_from_txt(data)