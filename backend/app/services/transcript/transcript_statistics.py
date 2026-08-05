"""
Statistics calculator for transcript processing and curriculum mapping.
"""

from __future__ import annotations

import logging
from typing import List
from pydantic import BaseModel, Field

from app.services.transcript.chunk_builder import ChunkData
from app.services.transcript.curriculum_mapper import MappingResult
from app.services.transcript.sentence_segmenter import SentenceItem

logger = logging.getLogger(__name__)


class TranscriptStatistics(BaseModel):
    total_sentences: int = 0
    total_chunks: int = 0
    mapped_chunks: int = 0
    unmapped_chunks: int = 0
    coverage_candidates: int = 0
    average_chunk_length_words: float = 0.0
    average_speaking_time_seconds: float = 0.0
    warnings: List[str] = Field(default_factory=list)


class TranscriptStatisticsCalculator:
    """Computes aggregate metrics for transcript chunks and mappings."""

    @staticmethod
    def calculate(
        sentences: List[SentenceItem],
        chunks: List[ChunkData],
        mappings: List[MappingResult],
        warnings: List[str],
    ) -> TranscriptStatistics:
        total_sentences = len(sentences)
        total_chunks = len(chunks)

        mapped_chunks = sum(1 for m in mappings if m.confidence_score >= 0.30)
        unmapped_chunks = total_chunks - mapped_chunks

        # Coverage candidates are mapped topics with confidence >= 0.60
        coverage_candidates = sum(1 for m in mappings if m.confidence_score >= 0.60)

        avg_words = (
            round(sum(c.word_count for c in chunks) / total_chunks, 1)
            if total_chunks > 0
            else 0.0
        )

        total_speaking_time = (
            chunks[-1].end_time - chunks[0].start_time
            if chunks
            else 0.0
        )
        avg_speaking_time = (
            round(total_speaking_time / total_chunks, 1)
            if total_chunks > 0
            else 0.0
        )

        return TranscriptStatistics(
            total_sentences=total_sentences,
            total_chunks=total_chunks,
            mapped_chunks=mapped_chunks,
            unmapped_chunks=unmapped_chunks,
            coverage_candidates=coverage_candidates,
            average_chunk_length_words=avg_words,
            average_speaking_time_seconds=avg_speaking_time,
            warnings=warnings,
        )
