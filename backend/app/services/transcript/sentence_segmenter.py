"""
Sentence segmenter for splitting transcript entries into individual sentences
while preserving exact timestamps and speaker attributes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Dict, Any

from app.services.transcript.transcript_cleaner import TranscriptCleaner

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


@dataclass(slots=True)
class SentenceItem:
    sentence_index: int
    speaker: str
    start: float
    end: float
    text: str


class SentenceSegmenter:
    """Segments raw transcript entry dicts into timestamped sentences."""

    @staticmethod
    def segment(transcript_items: List[Dict[str, Any]]) -> List[SentenceItem]:
        sentences: List[SentenceItem] = []
        idx = 1

        for item in transcript_items:
            raw_text = str(item.get("text", ""))
            cleaned_text = TranscriptCleaner.clean_text(raw_text)
            if not cleaned_text:
                continue

            speaker = str(item.get("speaker", "Faculty"))
            start = float(item.get("start", 0.0))
            end = float(item.get("end", 0.0))

            # Split into individual sentences if multiple sentences exist in entry
            parts = _SENTENCE_SPLIT_RE.split(cleaned_text)
            num_parts = len(parts)

            if num_parts <= 1 or end <= start:
                sentences.append(
                    SentenceItem(
                        sentence_index=idx,
                        speaker=speaker,
                        start=start,
                        end=end,
                        text=cleaned_text,
                    )
                )
                idx += 1
            else:
                # Interpolate timestamps proportionally for split sentences
                duration_per_part = (end - start) / num_parts
                for i, part_text in enumerate(parts):
                    p_start = round(start + (i * duration_per_part), 2)
                    p_end = round(p_start + duration_per_part, 2)
                    sentences.append(
                        SentenceItem(
                            sentence_index=idx,
                            speaker=speaker,
                            start=p_start,
                            end=p_end,
                            text=part_text.strip(),
                        )
                    )
                    idx += 1

        return sentences
