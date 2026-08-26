from __future__ import annotations

import logging
from typing import Dict, Any, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reference_chunk import ReferenceChunk
from app.models.reference_material import ReferenceMaterial
from app.services.rag.rag_retrieval_service import RAGRetrievalService, IndexingResultData

logger = logging.getLogger(__name__)


class RAGIndexingService:
    """
    Dedicated RAG Indexing Service managing reference material chunking,
    embedding generation, index persistence, status tracking, and deletion.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.retrieval_service = RAGRetrievalService(db)

    def index_reference_material(self, reference_material_id: UUID) -> IndexingResultData:
        """
        Indexes a reference document by chunking text, computing embeddings, and storing ReferenceChunk rows.
        Returns indexing summary metrics.
        """
        return self.retrieval_service.index_reference_material(reference_material_id)

    def reindex_reference_material(self, reference_material_id: UUID) -> IndexingResultData:
        """
        Atomically replaces/updates the index for an existing reference material.
        """
        return self.retrieval_service.index_reference_material(reference_material_id)

    def delete_reference_index(self, reference_material_id: UUID) -> Dict[str, Any]:
        """
        Deletes all ReferenceChunk rows associated with the specified reference material.
        """
        ref_doc = self.db.get(ReferenceMaterial, reference_material_id)
        if ref_doc is None:
            raise LookupError(f"Reference material '{reference_material_id}' not found")

        chunks = list(
            self.db.scalars(
                select(ReferenceChunk).where(
                    ReferenceChunk.reference_material_id == ref_doc.id
                )
            ).all()
        )
        deleted_count = len(chunks)
        for c in chunks:
            self.db.delete(c)

        ref_doc.processing_status = "UPLOADED"
        self.db.add(ref_doc)
        self.db.commit()

        logger.info("Deleted RAG index for reference material '%s' (%d chunks removed)", ref_doc.id, deleted_count)
        return {
            "reference_material_id": str(ref_doc.id),
            "status": "DELETED",
            "chunks_removed": deleted_count,
            "processing_status": ref_doc.processing_status,
        }

    def get_indexing_status(self, reference_material_id: UUID) -> Dict[str, Any]:
        """
        Retrieves real-time document indexing status and chunk metrics.
        """
        return self.retrieval_service.get_document_status(reference_material_id)
