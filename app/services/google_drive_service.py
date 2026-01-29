from __future__ import annotations

import json
import requests
from typing import Optional, Dict, Any

from fastapi import HTTPException

DRIVE_API = "https://www.googleapis.com/drive/v3"
DRIVE_UPLOAD_API = "https://www.googleapis.com/upload/drive/v3/files"

# Sprint 1: subpastas por categoria (nome amigável)
CATEGORY_FOLDERS = {
    "inicial": "Inicial",
    "procuracao": "Procuração",
    "contrato": "Contrato",
    "docs_cliente": "Docs do Cliente",
    "outros": "Outros",
}


def _auth_headers(access_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _raise_drive_error(r: requests.Response, prefix: str) -> None:
    # Drive costuma retornar JSON com {error:{message,...}}
    try:
        payload = r.json()
    except Exception:
        payload = {"raw": r.text}

    msg = payload.get("error", {}).get("message") if isinstance(payload, dict) else None
    detail = msg or payload or r.text
    raise HTTPException(status_code=400, detail=f"{prefix}: {detail}")


def find_folder(access_token: str, name: str, parent_folder_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Busca pasta por nome (e parent, se informado) pra evitar duplicar.
    """
    safe_name = name.replace("'", "\\'")
    q = [
        f"name='{safe_name}'",
        "mimeType='application/vnd.google-apps.folder'",
        "trashed=false",
    ]
    if parent_folder_id:
        q.append(f"'{parent_folder_id}' in parents")

    params = {
        "q": " and ".join(q),
        "fields": "files(id,name,webViewLink)",
        "pageSize": 1,
    }

    r = requests.get(
        f"{DRIVE_API}/files",
        headers=_auth_headers(access_token),
        params=params,
        timeout=30,
    )
    if r.status_code != 200:
        # se falhar busca, não trava o fluxo: só assume que não existe
        return None

    files = r.json().get("files", [])
    return files[0] if files else None


def ensure_folder(access_token: str, name: str, parent_folder_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Pega se existe, senão cria.
    """
    existing = find_folder(access_token, name, parent_folder_id)
    if existing:
        return existing
    return create_folder(access_token, name, parent_folder_id)


def create_folder(access_token: str, name: str, parent_folder_id: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_folder_id:
        payload["parents"] = [parent_folder_id]

    r = requests.post(
        f"{DRIVE_API}/files",
        headers={**_auth_headers(access_token), "Content-Type": "application/json"},
        params={"fields": "id,name,webViewLink"},
        json=payload,
        timeout=30,
    )
    if r.status_code not in (200, 201):
        _raise_drive_error(r, "Drive create_folder failed")
    return r.json()


def ensure_process_folder(access_token: str, folder_name: str) -> Dict[str, Any]:
    """
    Pasta raiz do processo no Meu Drive (sem parent).
    """
    return ensure_folder(access_token, folder_name, parent_folder_id=None)


def ensure_category_folder(access_token: str, process_folder_id: str, category_key: str) -> Dict[str, Any]:
    """
    Subpasta dentro da pasta do processo.
    """
    folder_name = CATEGORY_FOLDERS.get(category_key, CATEGORY_FOLDERS["outros"])
    return ensure_folder(access_token, folder_name, parent_folder_id=process_folder_id)


def upload_file(
    access_token: str,
    folder_id: str,
    file_bytes: bytes,
    file_name: str,
    mime_type: str,
) -> Dict[str, Any]:
    """
    Upload multipart/related (metadata + conteúdo)
    Retorna id + webViewLink pra abrir no navegador.
    """
    metadata = {"name": file_name, "parents": [folder_id]}

    boundary = "legalhub_boundary_123"
    body = (
        f"--{boundary}\r\n"
        "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--".encode("utf-8")

    headers = {
        **_auth_headers(access_token),
        "Content-Type": f"multipart/related; boundary={boundary}",
    }

    r = requests.post(
        DRIVE_UPLOAD_API,
        headers=headers,
        params={"uploadType": "multipart", "fields": "id,webViewLink,name,mimeType"},
        data=body,
        timeout=60,
    )
    if r.status_code not in (200, 201):
        _raise_drive_error(r, "Drive upload_file failed")

    return r.json()
