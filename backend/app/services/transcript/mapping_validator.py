"""
Validator for transcript chunks and curriculum mappings.
Performs structural checks and returns warnings without crashing execution.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any

from app.services.transcript.chunk_builder import ChunkData
from app.services.transcript.curriculum_mapper import MappingResult
from app.services.transcript.exceptions import EmptyTranscriptError

logger = logging.getLogger(__name__)


class MappingValidator:
    """Validates transcript payloads, chunks, and mappings."""

    @staticmethod
    def validate(
        raw_items: List[Dict[str, Any]],
        chunks: List[ChunkData],
        mappings: List[MappingResult],
    ) -> List[str]:
        warnings: List[str] = []

        if not raw_items:
            raise EmptyTranscriptError("Transcript payload contains no text items")

        # 1. Check timestamp validity
        for idx, item in enumerate(raw_items):
            start = float(item.get("start", 0.0))
            end = float(item.get("end", 0.0))
            if start < 0 or end < 0:
                warnings.append(f"Negative Timestamp: Entry {idx} has start={start}, end={end}")
            if end <= start and start > 0:
                warnings.append(f"Invalid Duration: Entry {idx} end time ({end}) is <= start time ({start})")

        # 2. Check for duplicate chunks
        seen_texts = set()
        for c in chunks:
            clean = c.text.strip().lower()
            if clean in seen_texts:
                warnings.append(f"Duplicate Chunk: Chunk {c.chunk_index} contains identical text to an earlier chunk")
            seen_texts.add(clean)

        # 3. Check low confidence / unmapped chunks
        unmapped_count = sum(1 for m in mappings if m.confidence_score < 0.30)
        if unmapped_count > 0:
            warnings.append(f"Unmapped Chunks: {unmapped_count} chunk(s) could not be mapped with confidence >= 0.30")

        logger.info("Transcript validation completed with %d warning(s)", len(warnings))
        return warnings
