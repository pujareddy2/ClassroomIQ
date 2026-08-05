"""
Deterministic curriculum mapper matching transcript chunks to curriculum segments
via keyword overlap, title matching, and hierarchy path matching.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Set
from uuid import UUID

from app.services.curriculum_hierarchy.hierarchy_models import CurriculumSegment
from app.services.transcript.chunk_builder import ChunkData

logger = logging.getLogger(__name__)

# Stopwords to filter out during keyword matching
STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what", "which",
    "this", "that", "these", "those", "then", "just", "so", "than", "such", "both",
    "through", "about", "for", "is", "of", "to", "in", "it", "you", "we", "can",
    "will", "should", "now", "here", "there", "have", "has", "had", "be", "been",
    "do", "does", "did", "say", "said", "talk", "talking", "today", "topic", "class",
}


@dataclass(slots=True)
class MappingResult:
    chunk_index: int
    curriculum_id: UUID
    unit_id: UUID
    unit_title: str
    chapter_id: UUID | None
    chapter_title: str | None
    topic_id: UUID
    topic_title: str
    confidence_score: float
    mapping_reason: str


class CurriculumMapper:
    """Deterministically maps transcript chunks to curriculum segments."""

    @staticmethod
    def _extract_keywords(text: str) -> Set[str]:
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        return {w for w in words if w not in STOPWORDS}

    @classmethod
    def map_chunks(
        self,
        chunks: List[ChunkData],
        segments: List[CurriculumSegment],
    ) -> List[MappingResult]:
        if not chunks or not segments:
            return []

        results: List[MappingResult] = []

        for chunk in chunks:
            chunk_keywords = self._extract_keywords(chunk.text)
            best_match: MappingResult | None = None
            highest_score = 0.0

            for seg in segments:
                # 1. Match against unit title
                unit_kw = self._extract_keywords(seg.unit_title)
                # 2. Match against chapter title
                chap_kw = self._extract_keywords(seg.chapter_title or "")
                # 3. Match against topic titles
                topic_kws = [self._extract_keywords(t) for t in seg.topic_titles]
                # 4. Match against outcomes
                outcome_kws = [self._extract_keywords(o) for o in seg.learning_outcomes]

                # Check exact topic title occurrences in chunk text
                for idx, t_title in enumerate(seg.topic_titles):
                    t_clean = t_title.strip().lower()
                    if t_clean and len(t_clean) > 3 and t_clean in chunk.text.lower():
                        score = 0.95
                        reason = f"Exact topic title match: '{t_title}'"
                        if score > highest_score:
                            highest_score = score
                            topic_id = seg.topic_ids[idx] if idx < len(seg.topic_ids) else seg.unit_id
                            best_match = MappingResult(
                                chunk_index=chunk.chunk_index,
                                curriculum_id=seg.curriculum_id,
                                unit_id=seg.unit_id,
                                unit_title=seg.unit_title,
                                chapter_id=seg.chapter_id,
                                chapter_title=seg.chapter_title,
                                topic_id=topic_id,
                                topic_title=t_title,
                                confidence_score=score,
                                mapping_reason=reason,
                            )

                # Keyword Jaccard Overlap
                all_seg_keywords = unit_kw | chap_kw
                for tk in topic_kws:
                    all_seg_keywords |= tk
                for ok in outcome_kws:
                    all_seg_keywords |= ok

                intersection = chunk_keywords & all_seg_keywords
                if all_seg_keywords and chunk_keywords:
                    overlap_ratio = len(intersection) / min(len(chunk_keywords), len(all_seg_keywords))
                    if overlap_ratio > 0.15:
                        score = round(min(0.90, 0.4 + overlap_ratio * 0.5), 2)
                        matched_words = ", ".join(list(intersection)[:5])
                        reason = f"Keyword overlap match ({len(intersection)} words: {matched_words})"
                        if score > highest_score:
                            highest_score = score
                            topic_id = seg.topic_ids[0] if seg.topic_ids else seg.unit_id
                            topic_title = seg.topic_titles[0] if seg.topic_titles else seg.unit_title
                            best_match = MappingResult(
                                chunk_index=chunk.chunk_index,
                                curriculum_id=seg.curriculum_id,
                                unit_id=seg.unit_id,
                                unit_title=seg.unit_title,
                                chapter_id=seg.chapter_id,
                                chapter_title=seg.chapter_title,
                                topic_id=topic_id,
                                topic_title=topic_title,
                                confidence_score=score,
                                mapping_reason=reason,
                            )

            if best_match is not None and highest_score >= 0.30:
                results.append(best_match)
            else:
                # Unmapped fallback record
                first_seg = segments[0]
                results.append(
                    MappingResult(
                        chunk_index=chunk.chunk_index,
                        curriculum_id=first_seg.curriculum_id,
                        unit_id=first_seg.unit_id,
                        unit_title=first_seg.unit_title,
                        chapter_id=first_seg.chapter_id,
                        chapter_title=first_seg.chapter_title,
                        topic_id=first_seg.unit_id,
                        topic_title="Unmapped / General Discussion",
                        confidence_score=0.10,
                        mapping_reason="Low keyword confidence (<0.30)",
                    )
                )

        logger.info("Curriculum mapping complete: %d/%d chunks mapped", sum(1 for r in results if r.confidence_score >= 0.30), len(chunks))
        return results
