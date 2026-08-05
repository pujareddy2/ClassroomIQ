"""
Teaching Structure Engine — Evaluates lecture organization and structural flow.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class StructureEngine:
    INTRO_PATTERNS = [
        r"\btoday we will\b",
        r"\bwelcome\b",
        r"\bagenda\b",
        r"\bin this lecture\b",
        r"\btopic for today\b",
        r"\blet's start\b",
        r"\bshall we begin\b",
    ]

    CONCLUSION_PATTERNS = [
        r"\bto summarize\b",
        r"\bin conclusion\b",
        r"\btoday we covered\b",
        r"\brecap\b",
        r"\bthat wraps up\b",
        r"\bquestions before we finish\b",
        r"\bnext time\b",
    ]

    TRANSITION_PATTERNS = [
        r"\bmoving on to\b",
        r"\bnext topic\b",
        r"\bnow let's look at\b",
        r"\bturning our attention to\b",
        r"\bhaving discussed\b",
    ]

    def analyze(self, transcript_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not transcript_chunks:
            return {
                "score": 0.0,
                "has_introduction": False,
                "has_conclusion": False,
                "topic_jump_count": 0,
                "improper_ordering_count": 0,
                "missing_transitions_count": 0,
                "continuity_score": 0.0,
                "detected_flow": [],
            }

        total_chunks = len(transcript_chunks)
        first_quarter = transcript_chunks[: max(1, total_chunks // 4)]
        last_quarter = transcript_chunks[max(0, 3 * total_chunks // 4) :]

        # 1. Introduction Detection
        intro_text = " ".join([c.get("text", "") for c in first_quarter])
        has_intro = any(re.search(p, intro_text, re.IGNORECASE) for p in self.INTRO_PATTERNS)

        # 2. Conclusion Detection
        conclusion_text = " ".join([c.get("text", "") for c in last_quarter])
        has_conclusion = any(re.search(p, conclusion_text, re.IGNORECASE) for p in self.CONCLUSION_PATTERNS)

        # 3. Transitions & Topic Continuity
        full_text = " ".join([c.get("text", "") for c in transcript_chunks])
        transition_matches = sum(len(re.findall(p, full_text, re.IGNORECASE)) for p in self.TRANSITION_PATTERNS)

        # Topic sequence tracking (if mapped topic_ids present)
        topic_sequence = [c.get("topic_id") for c in transcript_chunks if c.get("topic_id")]
        topic_jumps = 0
        improper_ordering = 0

        for i in range(1, len(topic_sequence)):
            if topic_sequence[i] != topic_sequence[i - 1]:
                topic_jumps += 1
                # Check for back-tracking (improper ordering)
                if topic_sequence[i] in topic_sequence[: i - 1]:
                    improper_ordering += 1

        missing_transitions = max(0, topic_jumps - transition_matches)

        # Calculate structure score (0-100)
        intro_score = 25.0 if has_intro else 0.0
        conclusion_score = 25.0 if has_conclusion else 0.0
        continuity_score = max(0.0, 50.0 - (topic_jumps * 2.0) - (improper_ordering * 5.0))
        transition_bonus = min(20.0, transition_matches * 5.0)

        score = round(min(100.0, intro_score + conclusion_score + continuity_score + transition_bonus), 1)

        detected_flow = []
        if has_intro:
            detected_flow.append("Introduction")
        detected_flow.extend(["Concept Explanation", "Examples & Applications"])
        if has_conclusion:
            detected_flow.append("Summary & Conclusion")

        return {
            "score": score,
            "has_introduction": has_intro,
            "has_conclusion": has_conclusion,
            "topic_jump_count": topic_jumps,
            "improper_ordering_count": improper_ordering,
            "missing_transitions_count": missing_transitions,
            "continuity_score": round(continuity_score, 1),
            "detected_flow": detected_flow,
        }
