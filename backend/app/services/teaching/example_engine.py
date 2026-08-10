"""
Example Detection Engine — Detects examples, categories, relevance, quality, and diversity.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List
from uuid import UUID

logger = logging.getLogger(__name__)


class ExampleEngine:
    EXAMPLE_PATTERNS = {
        "Real-world": [
            r"\bfor example\b",
            r"\bfor instance\b",
            r"\bin real life\b",
            r"\breal world\b",
            r"\beveryday life\b",
            r"\bpractical example\b",
        ],
        "Programming": [
            r"\bcode\b",
            r"\bsyntax\b",
            r"\bfunction\b",
            r"\bimplementation\b",
            r"\bvariable\b",
            r"\bclass\b",
            r"\bmethod\b",
            r"\bprogram\b",
            r"\bloop\b",
        ],
        "Industrial": [
            r"\bindustry\b",
            r"\bproduction\b",
            r"\benterprise\b",
            r"\bcompany\b",
            r"\bcommercial\b",
            r"\bdeployed in\b",
        ],
        "Case Study": [
            r"\bcase study\b",
            r"\bscenario\b",
            r"\bproblem statement\b",
            r"\breal case\b",
        ],
        "Numerical": [
            r"\bcalculate\b",
            r"\bformula\b",
            r"\bequals\b",
            r"\bsolve\b",
            r"\bvalue of\b",
            r"\blet's compute\b",
        ],
        "Analogy": [
            r"\blike a\b",
            r"\bsimilar to\b",
            r"\banalogy\b",
            r"\bthink of it as\b",
            r"\bjust as\b",
            r"\bmetaphor\b",
        ],
        "Counter-example": [
            r"\bnon-example\b",
            r"\bunlike\b",
            r"\bcontrast with\b",
            r"\bon the other hand\b",
            r"\bcounter example\b",
        ],
    }

    def analyze(self, transcript_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        detected_examples: List[Dict[str, Any]] = []
        types_found = set()

        for chunk in transcript_chunks:
            text = chunk.get("text", "")
            start_time = chunk.get("start_time", chunk.get("start", 0.0))
            end_time = chunk.get("end_time", chunk.get("end", 0.0))
            topic_id = chunk.get("topic_id")

            for example_type, patterns in self.EXAMPLE_PATTERNS.items():
                for pat in patterns:
                    if re.search(pat, text, re.IGNORECASE):
                        types_found.add(example_type)
                        relevance = 85.0 if topic_id else 75.0
                        quality = min(95.0, 60.0 + len(text.split()) * 0.5)

                        # Excerpt context sentence
                        sentences = [s.strip() for s in text.split(".") if s.strip()]
                        desc = sentences[0] if sentences else text[:150]

                        detected_examples.append(
                            {
                                "example_type": example_type,
                                "description": desc,
                                "relevance_score": round(relevance, 1),
                                "quality_score": round(quality, 1),
                                "timestamp_start": float(start_time),
                                "timestamp_end": float(end_time),
                                "topic_id": str(topic_id) if topic_id else None,
                            }
                        )
                        break  # Match one pattern per type per chunk

        example_count = len(detected_examples)
        diversity_count = len(types_found)

        # Calculate example score (0-100)
        if example_count == 0:
            score = 0.0
        else:
            base_score = min(70.0, example_count * 15.0)
            diversity_bonus = min(30.0, diversity_count * 10.0)
            score = round(base_score + diversity_bonus, 1)

        return {
            "score": score,
            "example_count": example_count,
            "example_diversity": diversity_count,
            "examples": detected_examples,
        }
