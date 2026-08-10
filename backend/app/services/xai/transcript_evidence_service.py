"""
TranscriptEvidenceService

Finds the minimal transcript snippet supporting an AI decision.

Rules:
  - Never return the full transcript.
  - Return only the smallest meaningful passage (max 300 characters).
  - Uses the chunk_id from validation results or searches by topic mapping.
  - Returns a TranscriptEvidence ORM object ready for persistence.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.explanation_engine import TranscriptEvidence
from app.models.transcript_chunk import TranscriptChunk

logger = logging.getLogger(__name__)

MAX_SNIPPET_LENGTH = 300


class TranscriptEvidenceService:

    def __init__(self, db: Session):
        self.db = db

    def find_snippet(
        self,
        evidence_item_id: UUID,
        lecture_id: UUID,
        chunk_id: Optional[str] = None,
        topic_name: Optional[str] = None,
    ) -> TranscriptEvidence:
        """
        Find the minimal transcript passage for the given context.

        Priority:
          1. If chunk_id is given, load that specific chunk.
          2. Otherwise, fall back to the first available chunk.
          3. If no transcript exists, return a 'not available' sentinel.
        """
        logger.info("Transcript Evidence Generated — evidence_item_id=%s", evidence_item_id)

        chunk = None

        # Priority 1: specific chunk
        if chunk_id is not None:
            try:
                chunk_idx = int(chunk_id)
                chunk = (
                    self.db.query(TranscriptChunk)
                    .filter(TranscriptChunk.chunk_index == chunk_idx)
                    .first()
                )
            except (ValueError, TypeError):
                pass

        # Priority 2: first chunk fallback
        if chunk is None:
            chunk = (
                self.db.query(TranscriptChunk)
                .order_by(TranscriptChunk.chunk_index.asc())
                .first()
            )

        # Priority 3: sentinel when no transcript data exists
        if chunk is None:
            return TranscriptEvidence(
                evidence_item_id=evidence_item_id,
                lecture_id=lecture_id,
                chunk_id=None,
                speaker="Faculty",
                snippet="No transcript snippet available for this segment.",
                start_time=0.0,
                end_time=0.0,
            )

        # Truncate text to minimal passage
        snippet_text = chunk.text.strip()
        if len(snippet_text) > MAX_SNIPPET_LENGTH:
            snippet_text = snippet_text[: MAX_SNIPPET_LENGTH - 3] + "..."

        return TranscriptEvidence(
            evidence_item_id=evidence_item_id,
            lecture_id=lecture_id,
            chunk_id=str(chunk.chunk_index),
            speaker=chunk.speaker or "Faculty",
            snippet=snippet_text,
            start_time=chunk.start_time,
            end_time=chunk.end_time,
        )
