from __future__ import annotations

import logging
import time
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.rag import (
    RAGChunkItemSchema,
    RAGChunksListResponse,
    RAGIndexResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGStatusResponse,
)
from app.schemas.response import ok
from app.services.rag.rag_indexing_service import RAGIndexingService
from app.services.rag.rag_retrieval_service import RAGRetrievalService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG Engine"])


@router.post(
    "/index/{reference_material_id}",
    status_code=status.HTTP_200_OK,
    summary="Index a reference document for RAG retrieval",
    description="Chunks and embeds an uploaded reference document using SHA-256 content hashing and atomic re-indexing.",
)
def index_document(
    reference_material_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start_ts = time.time()
    indexing_service = RAGIndexingService(db)
    try:
        res = indexing_service.index_reference_material(reference_material_id)
        elapsed = round(time.time() - start_ts, 2)
        response_data = RAGIndexResponse(
            status="SUCCESS",
            message="Reference material indexed successfully",
            reference_material_id=res.reference_material_id,
            chunks_created=res.chunks_created,
            total_words=0,
            embedding_dimension=384,
            retrieval_mode=indexing_service.retrieval_service.embedding_service.retrieval_mode,
            processing_time_seconds=elapsed,
            processing_status=res.processing_status,
        ).model_dump()
        return ok(
            data=response_data,
            message=f"Document '{res.document_title}' indexed into RAG vector store successfully.",
            start_ts=start_ts,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to index reference document for RAG")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {exc}",
        ) from exc


@router.post(
    "/query",
    status_code=status.HTTP_200_OK,
    summary="Query academic evidence via hybrid RAG retrieval",
    description="Executes 70% vector similarity + 20% keyword overlap + 10% metadata reranking with course-level data isolation.",
)
def query_evidence(
    payload: RAGQueryRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start_ts = time.time()
    service = RAGRetrievalService(db)
    try:
        bundle = service.retrieve_evidence(
            query=payload.query,
            course_id=payload.course_id,
            top_k=payload.top_k,
            topic_id=payload.topic_id,
            reference_material_id=payload.reference_material_id,
        )
        elapsed = round(time.time() - start_ts, 2)
        response_data = RAGQueryResponse(
            status="SUCCESS",
            query=bundle.query,
            total_results=bundle.total_results,
            retrieval_mode=service.embedding_service.retrieval_mode,
            processing_time_seconds=elapsed,
            evidence=[
                {
                    "chunk_id": item.chunk_id,
                    "reference_material_id": item.reference_material_id,
                    "document_title": item.document_title,
                    "author": item.author,
                    "edition": item.edition,
                    "page_number": item.page_number,
                    "section_title": item.section_title,
                    "chunk_text": item.chunk_text,
                    "vector_score": item.vector_score,
                    "keyword_score": item.keyword_score,
                    "final_score": item.final_score,
                }
                for item in bundle.evidence
            ],
        ).model_dump()
        return ok(
            data=response_data,
            message=f"{bundle.total_results} relevant evidence chunk(s) retrieved.",
            start_ts=start_ts,
        )
    except Exception as exc:
        logger.exception("Failed to execute RAG query")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query failed: {exc}",
        ) from exc


@router.get(
    "/documents/{reference_material_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Get document indexing status",
    description="Returns current document status (UPLOADED, CHUNKING, EMBEDDED, INDEXED, INDEXING_FAILED) and chunk count.",
)
def get_document_status(
    reference_material_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start_ts = time.time()
    service = RAGRetrievalService(db)
    try:
        status_data = service.get_document_status(reference_material_id)
        response_data = RAGStatusResponse(
            status="SUCCESS",
            reference_material_id=UUID(status_data["reference_material_id"]),
            processing_status=status_data["processing_status"],
            total_chunks=status_data["chunk_count"],
            embedded_chunks=status_data["chunk_count"],
            failed_chunks=0,
            embedding_dimension=384,
            retrieval_mode=service.embedding_service.retrieval_mode,
        ).model_dump()
        return ok(
            data=response_data,
            message="Document status retrieved.",
            start_ts=start_ts,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/documents/{reference_material_id}/chunks",
    status_code=status.HTTP_200_OK,
    summary="Get all indexed chunks for a reference document",
    description="Returns all active ReferenceChunk rows for the specified reference material ID.",
)
def get_document_chunks(
    reference_material_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start_ts = time.time()
    service = RAGRetrievalService(db)
    chunks = service.get_document_chunks(reference_material_id)
    chunk_items = [
        RAGChunkItemSchema(
            chunk_id=c.id,
            chunk_index=c.chunk_index,
            section_title=c.section_title,
            page_number=c.page_number,
            word_count=c.word_count,
            chunk_text=c.chunk_text,
            has_embedding=c.embedding is not None,
            status=c.status,
        ).model_dump()
        for c in chunks
    ]
    response_data = RAGChunksListResponse(
        status="SUCCESS",
        reference_material_id=reference_material_id,
        total_chunks=len(chunk_items),
        chunks=chunk_items,
    ).model_dump()
    return ok(
        data=response_data,
        message=f"Retrieved {len(chunk_items)} chunk(s) for document.",
        start_ts=start_ts,
    )


@router.post(
    "/reindex/{reference_material_id}",
    status_code=status.HTTP_200_OK,
    summary="Re-index a reference document (Admin/Development)",
    description="Forces a complete atomic re-indexing of a reference document.",
)
def reindex_document(
    reference_material_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start_ts = time.time()
    indexing_service = RAGIndexingService(db)
    try:
        res = indexing_service.reindex_reference_material(reference_material_id)
        elapsed = round(time.time() - start_ts, 2)
        response_data = RAGIndexResponse(
            status="SUCCESS",
            message="Reference material re-indexed successfully",
            reference_material_id=res.reference_material_id,
            chunks_created=res.chunks_created,
            total_words=0,
            embedding_dimension=384,
            retrieval_mode=indexing_service.retrieval_service.embedding_service.retrieval_mode,
            processing_time_seconds=elapsed,
            processing_status=res.processing_status,
        ).model_dump()
        return ok(
            data=response_data,
            message=f"Document '{res.document_title}' re-indexed successfully.",
            start_ts=start_ts,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to re-index document")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Re-indexing failed: {exc}",
        ) from exc
