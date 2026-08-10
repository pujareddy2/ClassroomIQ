"""
Semantic chunk builder for grouping sentences into natural teaching chunks
based on speaker turns, time windows (30-90s), and word count thresholds (60-150 words).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from app.services.transcript.sentence_segmenter import SentenceItem

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ChunkData:
    chunk_index: int
    start_time: float
    end_time: float
    speaker: str
    text: str
    sentence_count: int
    word_count: int


class SemanticChunkBuilder:
    """Groups sentences into natural semantic chunks following teaching flow."""

    @staticmethod
    def build_chunks(
        sentences: List[SentenceItem],
        max_duration_seconds: float = 75.0,
        max_word_count: int = 140,
    ) -> List[ChunkData]:
        if not sentences:
            return []

        chunks: List[ChunkData] = []
        chunk_idx = 1

        current_sentences: List[SentenceItem] = []
        current_word_count = 0
        current_speaker: str | None = None
        chunk_start_time: float = sentences[0].start

        for s in sentences:
            words = s.text.split()
            word_len = len(words)

            # Check if we should flush current chunk:
            # 1. Speaker changed
            # 2. Total duration > max_duration_seconds
            # 3. Total word count > max_word_count
            speaker_changed = current_speaker is not None and current_speaker != s.speaker
            duration_exceeded = (s.end - chunk_start_time) >= max_duration_seconds
            words_exceeded = (current_word_count + word_len) > max_word_count

            if current_sentences and (speaker_changed or duration_exceeded or words_exceeded):
                # Flush chunk
                chunk_text = " ".join([st.text for st in current_sentences])
                chunks.append(
                    ChunkData(
                        chunk_index=chunk_idx,
                        start_time=chunk_start_time,
                        end_time=current_sentences[-1].end,
                        speaker=current_speaker or "Faculty",
                        text=chunk_text,
                        sentence_count=len(current_sentences),
                        word_count=current_word_count,
                    )
                )
                chunk_idx += 1

                # Reset
                current_sentences = []
                current_word_count = 0
                chunk_start_time = s.start

            current_sentences.append(s)
            current_word_count += word_len
            current_speaker = s.speaker

        # Flush last chunk
        if current_sentences:
            chunk_text = " ".join([st.text for st in current_sentences])
            chunks.append(
                ChunkData(
                    chunk_index=chunk_idx,
                    start_time=chunk_start_time,
                    end_time=current_sentences[-1].end,
                    speaker=current_speaker or "Faculty",
                    text=chunk_text,
                    sentence_count=len(current_sentences),
                    word_count=current_word_count,
                )
            )

        logger.info("Semantic chunking complete: %d chunk(s) created from %d sentence(s)", len(chunks), len(sentences))
        return chunks
