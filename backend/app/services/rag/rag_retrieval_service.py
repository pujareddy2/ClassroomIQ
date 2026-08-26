from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reference_chunk import ReferenceChunk
from app.models.reference_material import ReferenceMaterial
from app.models.topic import Topic
from app.models.topic_reference import TopicReference
from app.services.document_extractor.service import DocumentExtractionService
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.semantic_chunker import SemanticChunker

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RAGEvidenceItemData:
    chunk_id: UUID
    reference_material_id: UUID
    document_title: str
    author: Optional[str]
    edition: Optional[str]
    page_number: Optional[int]
    section_title: Optional[str]
    chunk_text: str
    vector_score: float
    keyword_score: float
    final_score: float


@dataclass(slots=True)
class RAGEvidenceBundleData:
    query: str
    total_results: int
    evidence: List[RAGEvidenceItemData]


@dataclass(slots=True)
class IndexingResultData:
    reference_material_id: UUID
    document_title: str
    processing_status: str
    chunks_created: int
    chunks_updated: int
    chunks_skipped: int


class RAGRetrievalService:
    """
    RAG Hybrid Retrieval Service:
    - Atomically indexes reference documents using SHA-256 content hashing.
    - Performs hybrid multi-signal similarity search (70% Vector + 20% Keyword + 10% Metadata).
    - Enforces course-level data isolation for multi-tenant security.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.chunker = SemanticChunker()
        self.embedding_service = EmbeddingService()

    def index_reference_material(self, reference_material_id: UUID) -> IndexingResultData:
        """
        Extracts, chunks, embeds, and atomically persists ReferenceChunk rows into PostgreSQL.
        Uses SHA-256 content hashing to reuse embeddings for unchanged text.
        """
        ref_doc = self.db.get(ReferenceMaterial, reference_material_id)
        if ref_doc is None:
            raise LookupError(f"Reference material '{reference_material_id}' not found")

        try:
            # 1. Extract raw text from disk file
            extractor = DocumentExtractionService(self.db)
            extracted = extractor.extract_text_from_path(ref_doc.file_path)
            raw_text = extracted.text

            if not raw_text or not raw_text.strip():
                ref_doc.processing_status = "INDEXING_FAILED"
                self.db.add(ref_doc)
                self.db.commit()
                raise ValueError("Document contains no text content to index")

            # 2. Semantic Chunking
            parsed_chunks = self.chunker.chunk_text(raw_text, document_title=ref_doc.title)
            if not parsed_chunks:
                ref_doc.processing_status = "INDEXING_FAILED"
                self.db.add(ref_doc)
                self.db.commit()
                raise ValueError("No semantic chunks could be created from document")

            # 3. Existing chunks map by hash for fast lookup
            existing_chunks = list(
                self.db.scalars(
                    select(ReferenceChunk).where(
                        ReferenceChunk.reference_material_id == ref_doc.id,
                        ReferenceChunk.status == "ACTIVE",
                    )
                ).all()
            )
            existing_hash_map = {c.content_hash: c for c in existing_chunks if c.content_hash}

            chunks_created = 0
            chunks_updated = 0
            chunks_skipped = 0

            # Delete old chunks that are no longer part of document
            for old_c in existing_chunks:
                self.db.delete(old_c)
            self.db.flush()

            # 4. Atomic indexing with content hash verification
            for p_chunk in parsed_chunks:
                c_hash = hashlib.sha256(p_chunk.chunk_text.encode("utf-8")).hexdigest()

                if c_hash in existing_hash_map and existing_hash_map[c_hash].embedding:
                    # Reuse existing embedding vector to save compute
                    emb_vector = existing_hash_map[c_hash].embedding
                    chunks_skipped += 1
                else:
                    emb_vector = self.embedding_service.generate_embedding(p_chunk.chunk_text)
                    chunks_created += 1

                row = ReferenceChunk(
                    reference_material_id=ref_doc.id,
                    course_id=ref_doc.course_id,
                    chunk_index=p_chunk.chunk_index,
                    section_title=p_chunk.section_title,
                    page_number=p_chunk.page_number,
                    chunk_text=p_chunk.chunk_text,
                    word_count=p_chunk.word_count,
                    token_count=p_chunk.token_count,
                    content_hash=c_hash,
                    embedding=emb_vector,
                    status="ACTIVE",
                )
                self.db.add(row)

            ref_doc.processing_status = "EMBEDDED"
            self.db.add(ref_doc)
            self.db.flush()
            self.db.commit()

            logger.info(
                "Successfully indexed reference material '%s' (%d created, %d reused)",
                ref_doc.id,
                chunks_created,
                chunks_skipped,
            )
            return IndexingResultData(
                reference_material_id=ref_doc.id,
                document_title=ref_doc.title,
                processing_status=ref_doc.processing_status,
                chunks_created=chunks_created + chunks_skipped,
                chunks_updated=chunks_updated,
                chunks_skipped=chunks_skipped,
            )

        except Exception as exc:
            logger.error("Failed to index reference material '%s': %s", ref_doc.id, exc)
            ref_doc.processing_status = "INDEXING_FAILED"
            self.db.add(ref_doc)
            self.db.commit()
            raise

    def retrieve_evidence(
        self,
        query: str,
        course_id: Optional[UUID] = None,
        top_k: int = 5,
        topic_id: Optional[UUID] = None,
        reference_material_id: Optional[UUID] = None,
    ) -> RAGEvidenceBundleData:
        """
        Executes multi-signal hybrid search:
        - 70% Dense Vector Similarity
        - 20% Technical Keyword Overlap
        - 10% Metadata / Title Boost
        Strictly isolated by course_id when provided.
        """
        clean_query = query.strip()
        if not clean_query:
            return RAGEvidenceBundleData(query=query, total_results=0, evidence=[])

        query_vector = self.embedding_service.generate_embedding(clean_query)
        stop_words = {"a", "an", "the", "and", "or", "but", "if", "is", "are", "was", "were", "of", "to", "in", "on", "for", "with", "by", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "from", "up", "down", "out", "off", "over", "under", "again", "further", "then", "once", "what", "where", "how", "why", "who", "which"}
        raw_words = re.findall(r"\w+", clean_query.lower())
        query_words = set(w for w in raw_words if w not in stop_words and len(w) > 1)
        if not query_words:
            query_words = set(raw_words)

        # Base candidate selection with course isolation
        stmt = select(ReferenceChunk).join(ReferenceChunk.reference_material).where(
            ReferenceChunk.status == "ACTIVE"
        )

        if course_id is not None:
            stmt = stmt.where(ReferenceChunk.course_id == course_id)

        if reference_material_id is not None:
            stmt = stmt.where(ReferenceChunk.reference_material_id == reference_material_id)
        elif topic_id is not None:
            stmt = stmt.join(
                TopicReference,
                TopicReference.reference_material_id == ReferenceChunk.reference_material_id,
            ).where(TopicReference.topic_id == topic_id)

        candidates = list(self.db.scalars(stmt).all())
        if not candidates and course_id is None:
            # Fallback if no course filter specified
            stmt_fallback = select(ReferenceChunk).where(ReferenceChunk.status == "ACTIVE")
            candidates = list(self.db.scalars(stmt_fallback).all())

        scored_items: List[tuple[ReferenceChunk, float, float, float]] = []

        for candidate in candidates:
            # 1. Dense Vector Similarity (70%)
            v_score = 0.0
            if candidate.embedding and isinstance(candidate.embedding, list):
                v_score = self.embedding_service.cosine_similarity(query_vector, candidate.embedding)

            # 2. Technical Keyword Overlap (20%)
            chunk_words = set(re.findall(r"\w+", candidate.chunk_text.lower()))
            overlap = len(query_words.intersection(chunk_words))
            k_score = (overlap / max(1, len(query_words))) if query_words else 0.0

            # 3. Metadata / Title Match (10%)
            m_score = 0.0
            if candidate.section_title and any(w in candidate.section_title.lower() for w in query_words):
                m_score = 1.0

            # Hybrid composite score
            final_score = (0.7 * v_score) + (0.2 * k_score) + (0.1 * m_score)
            scored_items.append((candidate, round(v_score, 4), round(k_score, 4), round(final_score, 4)))

        # Sort by final hybrid score descending
        scored_items.sort(key=lambda x: x[3], reverse=True)
        top_items = scored_items[:top_k]

        evidence_list: List[RAGEvidenceItemData] = []
        for chunk, v_s, k_s, f_s in top_items:
            ref_mat = chunk.reference_material
            evidence_list.append(
                RAGEvidenceItemData(
                    chunk_id=chunk.id,
                    reference_material_id=chunk.reference_material_id,
                    document_title=ref_mat.title if ref_mat else "Reference Document",
                    author=ref_mat.author if ref_mat else None,
                    edition=ref_mat.edition if ref_mat else None,
                    page_number=chunk.page_number,
                    section_title=chunk.section_title,
                    chunk_text=chunk.chunk_text,
                    vector_score=v_s,
                    keyword_score=k_s,
                    final_score=f_s,
                )
            )

        return RAGEvidenceBundleData(
            query=clean_query,
            total_results=len(evidence_list),
            evidence=evidence_list,
        )

    def get_document_status(self, reference_material_id: UUID) -> dict:
        """Returns document indexing status and chunk count."""
        ref_doc = self.db.get(ReferenceMaterial, reference_material_id)
        if ref_doc is None:
            raise LookupError(f"Reference material '{reference_material_id}' not found")

        count_stmt = select(ReferenceChunk).where(
            ReferenceChunk.reference_material_id == ref_doc.id,
            ReferenceChunk.status == "ACTIVE",
        )
        chunks_count = len(list(self.db.scalars(count_stmt).all()))

        return {
            "reference_material_id": str(ref_doc.id),
            "document_title": ref_doc.title,
            "processing_status": ref_doc.processing_status,
            "chunk_count": chunks_count,
            "updated_at": ref_doc.updated_at.isoformat() if ref_doc.updated_at else None,
        }

    def get_document_chunks(self, reference_material_id: UUID) -> List[ReferenceChunk]:
        """Returns all indexed ReferenceChunk rows for a document."""
        stmt = (
            select(ReferenceChunk)
            .where(
                ReferenceChunk.reference_material_id == reference_material_id,
                ReferenceChunk.status == "ACTIVE",
            )
            .order_by(ReferenceChunk.chunk_index.asc())
        )
        return list(self.db.scalars(stmt).all())
