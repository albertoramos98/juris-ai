import json
from datetime import datetime

import numpy as np
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.chunk_embedding import ChunkEmbedding
from app.models.process import Process
from app.models.global_knowledge import GlobalKnowledge

from app.services.google_oauth import get_valid_access_token
from app.services.drive_text_extractor import extract_text_from_drive_file
from app.services.openai_service import (
    embed_texts,
    answer_with_sources,
    compose_attack_defense_json,
    generate_petition_json,
)


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []

    chunks = []
    i = 0
    while i < len(text):
        end = min(len(text), i + max_chars)
        chunks.append(text[i:end])
        if end == len(text):
            break
        i = max(0, end - overlap)
    return chunks


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def index_process(db: Session, office_id: int, process_id: int) -> dict:
    proc = (
        db.query(Process)
        .filter(Process.office_id == office_id, Process.id == process_id)
        .first()
    )
    if not proc:
        return {"ok": False, "indexed": False, "error": "Process not found."}

    docs = (
        db.query(Document)
        .filter(
            Document.office_id == office_id,
            Document.process_id == process_id,
        )
        .order_by(Document.id.asc())
        .all()
    )

    # limpa índice anterior
    db.query(ChunkEmbedding).filter(
        ChunkEmbedding.office_id == office_id,
        ChunkEmbedding.process_id == process_id,
    ).delete(synchronize_session=False)

    db.query(DocumentChunk).filter(
        DocumentChunk.office_id == office_id,
        DocumentChunk.process_id == process_id,
    ).delete(synchronize_session=False)

    proc.rag_indexed_at = None
    proc.rag_chunk_count = 0

    db.commit()

    created_chunks: list[DocumentChunk] = []

    # Tenta pegar token do Google, mas não trava se falhar (pode estar expirado)
    access_token = None
    try:
        access_token = get_valid_access_token(db, office_id)
    except Exception as e:
        print(f"Aviso: Não foi possível obter token Google para o office {office_id}: {e}")

    docs_to_update: list[Document] = []

    for doc in docs:
        text = (doc.content_text or "").strip()

        # fallback: extrair do Drive SOMENTE se tiver token e estiver sem texto
        if not text and access_token:
            try:
                text = extract_text_from_drive_file(
                    access_token=access_token,
                    drive_file_id=doc.drive_file_id,
                    mime_type=doc.mime_type,
                ).strip()

                if text:
                    doc.content_text = text
                    docs_to_update.append(doc)

            except Exception:
                text = ""

        if not text:
            continue

        pieces = chunk_text(text)
        for idx, content in enumerate(pieces):
            ch = DocumentChunk(
                office_id=office_id,
                process_id=process_id,
                document_id=doc.id,
                chunk_index=idx,
                content=content,
            )
            db.add(ch)
            db.flush()
            created_chunks.append(ch)

    if docs_to_update:
        db.add_all(docs_to_update)

    db.commit()

    if not created_chunks:
        return {
            "ok": True,
            "indexed": False,
            "documents": len(docs),
            "chunks": 0,
            "detail": "Nenhum documento com texto indexável.",
        }

    try:
        # Processa em lotes para evitar limites da OpenAI
        all_texts = [c.content for c in created_chunks]
        batch_size = 100
        vectors = []
        for i in range(0, len(all_texts), batch_size):
            batch = all_texts[i : i + batch_size]
            vectors.extend(embed_texts(batch))
            
    except Exception as e:
        print(f"Erro ao gerar embeddings para o processo {process_id}: {e}")
        return {
            "ok": False,
            "indexed": False,
            "error": f"Falha na API da OpenAI ao gerar vetores: {str(e)}"
        }

    for ch, vec in zip(created_chunks, vectors):
        emb = ChunkEmbedding(
            office_id=office_id,
            process_id=process_id,
            document_id=ch.document_id,
            chunk_id=ch.id,
            embedding_json=json.dumps(vec),
        )
        db.add(emb)

    proc.rag_indexed_at = datetime.utcnow()
    proc.rag_chunk_count = len(created_chunks)

    db.commit()

    return {
        "ok": True,
        "indexed": True,
        "documents": len(docs),
        "chunks": len(created_chunks),
    }


def query_process(
    db: Session,
    office_id: int,
    process_id: int,
    question: str,
    top_k: int = 6,
) -> dict:
    proc = (
        db.query(Process)
        .filter(Process.office_id == office_id, Process.id == process_id)
        .first()
    )

    if not proc or not proc.rag_indexed_at or (proc.rag_chunk_count or 0) == 0:
        return {"ok": False, "error": "Processo ainda não indexado."}

    q_vec = np.array(embed_texts([question])[0], dtype=np.float32)

    rows = (
        db.query(ChunkEmbedding, DocumentChunk, Document)
        .join(DocumentChunk, DocumentChunk.id == ChunkEmbedding.chunk_id)
        .join(Document, Document.id == ChunkEmbedding.document_id)
        .filter(
            ChunkEmbedding.office_id == office_id,
            ChunkEmbedding.process_id == process_id,
        )
        .all()
    )

    if not rows:
        proc.rag_indexed_at = None
        proc.rag_chunk_count = 0
        db.commit()
        return {"ok": False, "error": "Processo ainda não indexado."}

    scored = []
    for emb, ch, doc in rows:
        vec = np.array(json.loads(emb.embedding_json), dtype=np.float32)
        score = _cosine(q_vec, vec)
        scored.append((score, ch, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:max(1, top_k)]

    sources = []
    context_blocks = []

    for score, ch, doc in top:
        excerpt = ch.content[:900]
        sources.append(
            {
                "score": float(score),
                "document_id": doc.id,
                "category": doc.category,
                "chunk_id": ch.id,
                "excerpt": excerpt,
                "drive_web_view_link": doc.drive_web_view_link,
            }
        )
        context_blocks.append(f"[Documento {doc.id} | {doc.category}]\n{excerpt}")

    answer = answer_with_sources(question, context_blocks)

    return {
        "ok": True,
        "answer": answer,
        "sources": sources,
    }


def _retrieve_top_chunks(
    db: Session,
    office_id: int,
    process_id: int,
    question: str,
    top_k: int,
) -> tuple[list[dict], list[str]]:
    """
    Retorna (sources, context_blocks) mesclando informações locais do processo 
    e informações globais do escritório (Jurisprudência/Doutrina).
    """
    q_vec = np.array(embed_texts([question])[0], dtype=np.float32)

    # 1. Busca Local (Fatos do Processo)
    local_rows = (
        db.query(ChunkEmbedding, DocumentChunk, Document)
        .join(DocumentChunk, DocumentChunk.id == ChunkEmbedding.chunk_id)
        .join(Document, Document.id == ChunkEmbedding.document_id)
        .filter(
            ChunkEmbedding.office_id == office_id,
            ChunkEmbedding.process_id == process_id,
        )
        .all()
    )

    scored_local = []
    if local_rows:
        for emb, ch, doc in local_rows:
            vec = np.array(json.loads(emb.embedding_json), dtype=np.float32)
            score = _cosine(q_vec, vec)
            # Pequeno boost para fatos locais do processo (prioridade sobre doutrina)
            scored_local.append((score + 0.1, ch.content, f"[Documento do Processo | {doc.category}]"))

    # 2. Busca Global (Fundamentação Jurídica)
    # Limitamos para evitar carregar milhares de linhas se a base crescer
    global_rows = (
        db.query(GlobalKnowledge)
        .filter(
            GlobalKnowledge.office_id == office_id,
            GlobalKnowledge.embedding_json.isnot(None)
        )
        .limit(500)
        .all()
    )

    scored_global = []
    if global_rows:
        for gk in global_rows:
            vec = np.array(json.loads(gk.embedding_json), dtype=np.float32)
            score = _cosine(q_vec, vec)
            scored_global.append((score, gk.content_text, f"[Base de Conhecimento | {gk.category}] {gk.title}"))

    # Mescla e ordena
    all_scored = scored_local + scored_global
    all_scored.sort(key=lambda x: x[0], reverse=True)
    
    top = all_scored[:max(1, top_k)]

    sources = []
    context_blocks = []

    for idx, (score, content, meta_info) in enumerate(top):
        excerpt = (content or "")[:1500]
        sources.append(
            {
                "score": float(score),
                "type": "global" if "Base de Conhecimento" in meta_info else "local",
                "meta": meta_info,
                "excerpt": excerpt,
            }
        )
        context_blocks.append(f"{meta_info}\n{excerpt}")

    return sources, context_blocks


def compose_process(
    db: Session,
    office_id: int,
    process_id: int,
    mode: str,  # "attack" | "defense"
    style: str = "formal",
    top_k: int = 10,
    notes: str = "",
    has_audio: bool = False,
    audio_notes: str = "",
    calculation_value: str = "",
) -> dict:
    proc = (
        db.query(Process)
        .filter(Process.office_id == office_id, Process.id == process_id)
        .first()
    )

    if not proc or not proc.rag_indexed_at or (proc.rag_chunk_count or 0) == 0:
        return {"ok": False, "detail": "Processo ainda não indexado."}

    anchor_q = (
        "Recupere fatos, pedidos, provas e pontos relevantes para montar uma petição inicial."
        if mode == "attack"
        else
        "Recupere resumo da inicial, pedidos do autor, pontos atacáveis, contradições e teses relevantes para montar uma contestação."
    )

    sources, context_blocks = _retrieve_top_chunks(
        db=db,
        office_id=office_id,
        process_id=process_id,
        question=anchor_q,
        top_k=top_k,
    )

    if not context_blocks:
        return {"ok": False, "detail": "Processo ainda não indexado."}

    # Adiciona notas de áudio se houver
    if has_audio and audio_notes:
        notes = f"{notes}\n\n[IMPORTANTE: EXISTE PROVA EM ÁUDIO]\nConteúdo do áudio: {audio_notes}\nUse isso como prova crucial na estratégia."

    # Adiciona valor da causa/cálculos
    if calculation_value:
        notes = f"{notes}\n\n[VALOR DA CAUSA / CÁLCULOS: {calculation_value}]\nUse este valor exato na seção de pedidos e valor da causa."

    composition = compose_attack_defense_json(
        mode=mode,
        style=style,
        notes=notes,
        context_blocks=context_blocks,
        client_name=proc.client.name if proc.client else ""
    )

    return {
        "ok": True,
        "mode": mode,
        "style": style,
        "composition": composition,
        "sources": sources,
    }


def generate_petition_draft(
    db: Session,
    office_id: int,
    process_id: int,
    mode: str,  # "attack" | "defense"
    style: str = "formal",
    top_k: int = 10,
    notes: str = "",
    has_audio: bool = False,
    audio_notes: str = "",
    calculation_value: str = "",
) -> dict:
    proc = (
        db.query(Process)
        .filter(Process.office_id == office_id, Process.id == process_id)
        .first()
    )

    if not proc or not proc.rag_indexed_at or (proc.rag_chunk_count or 0) == 0:
        return {"ok": False, "detail": "Processo ainda não indexado."}

    anchor_q = (
        "Recupere fatos, pedidos, fundamentos, provas e documentos relevantes para redigir uma PETIÇÃO INICIAL."
        if mode == "attack"
        else
        "Recupere resumo da inicial, pedidos do autor, pontos atacáveis, teses defensivas, lacunas documentais e fundamentos para redigir uma CONTESTAÇÃO."
    )

    sources, context_blocks = _retrieve_top_chunks(
        db=db,
        office_id=office_id,
        process_id=process_id,
        question=anchor_q,
        top_k=top_k,
    )

    if not context_blocks:
        return {"ok": False, "detail": "Processo ainda não indexado."}

    # Injeção de áudio na petição
    if has_audio and audio_notes:
        notes = f"{notes}\n\n[EVIDÊNCIA DE ÁUDIO]\nTranscrição/Resumo: {audio_notes}\nInclua uma seção específica ou mencione fortemente este áudio nos fatos e provas."

    # Injeção de valor da causa
    if calculation_value:
        notes = f"{notes}\n\n[VALOR DA CAUSA ATUALIZADO: {calculation_value}]\nCertifique-se de que o Valor da Causa e a liquidação dos pedidos somem exatamente este valor."

    draft_json = generate_petition_json(
        mode=mode,
        style=style,
        notes=notes,
        context_blocks=context_blocks,
        client_name=proc.client.name if proc.client else ""
    )

    return {
        "ok": True,
        "mode": mode,
        "style": style,
        "draft": draft_json,
        "sources": sources,
    }