"""
Partial Coverage Calculator component for Curriculum Coverage Intelligence Engine.
Computes fine-grained percentage completion (0.0% to 100.0%) for topics based on keyword presence and occurrence density.
"""

from __future__ import annotations

import re
from typing import List


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    stopwords = {"the", "a", "an", "and", "or", "in", "on", "of", "to", "for", "is", "are", "with"}
    return {w for w in words if w not in stopwords and len(w) > 2}


class PartialCoverageCalculator:
    """Calculates granular percentage coverage (0.0 to 100.0) for a curriculum topic."""

    @staticmethod
    def calculate_percentage(
        topic_name: str,
        subtopic_names: List[str],
        matching_chunks: List[dict],
    ) -> float:
        if not matching_chunks:
            return 0.0

        combined_text = " ".join(c["text"] for c in matching_chunks).lower()
        chunk_tokens = _tokenize(combined_text)

        # Base 1: Topic title containment
        topic_tokens = _tokenize(topic_name)
        topic_match_ratio = 0.0
        if topic_tokens:
            overlap = topic_tokens.intersection(chunk_tokens)
            topic_match_ratio = len(overlap) / float(len(topic_tokens))

        # Base 2: Subtopics covered ratio
        subtopic_covered_count = 0
        if subtopic_names:
            for sub in subtopic_names:
                sub_toks = _tokenize(sub)
                if sub_toks and sub_toks.issubset(chunk_tokens):
                    subtopic_covered_count += 1
                elif sub.lower() in combined_text:
                    subtopic_covered_count += 1
            subtopic_ratio = subtopic_covered_count / float(len(subtopic_names))
        else:
            subtopic_ratio = topic_match_ratio

        # Base 3: Explanation depth factor (number of words / sentences)
        word_count = len(combined_text.split())
        depth_factor = min(1.0, word_count / 40.0)

        # Composite percentage formula
        raw_pct = (0.4 * topic_match_ratio + 0.4 * subtopic_ratio + 0.2 * depth_factor) * 100.0
        return round(min(100.0, max(10.0, raw_pct)), 1)
