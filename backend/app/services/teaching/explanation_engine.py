"""
Explanation Quality Engine — Deterministic analysis + Gemini Flash qualitative feedback.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ExplanationEngine:
    def analyze(self, transcript_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        full_text = " ".join([c.get("text", "") for c in transcript_chunks])
        if not full_text.strip():
            return {
                "score": 0.0,
                "definition_quality": 0.0,
                "concept_completeness": 0.0,
                "logical_progression": 0.0,
                "step_by_step_clarity": 0.0,
                "coherence_score": 0.0,
                "redundancy_score": 100.0,
                "strengths": ["No transcript text to analyze."],
                "weaknesses": ["Empty transcript content."],
                "qualitative_summary": "No explanation could be analyzed due to an empty transcript.",
            }

        # 1. Definition quality
        def_patterns = [
            r"\bis defined as\b",
            r"\brefers to\b",
            r"\bmeans that\b",
            r"\bconcept of\b",
            r"\bstands for\b",
            r"\bwhat is\b",
            r"\bin simple terms\b",
        ]
        def_matches = sum(len(re.findall(p, full_text, re.IGNORECASE)) for p in def_patterns)
        definition_quality = min(100.0, def_matches * 25.0 + 30.0)

        # 2. Step-by-step clarity & logical progression
        step_patterns = [
            r"\bfirst\b",
            r"\bsecond\b",
            r"\bnext\b",
            r"\bthen\b",
            r"\bfinally\b",
            r"\bstep\b",
            r"\btherefore\b",
            r"\bbecause\b",
            r"\bas a result\b",
            r"\bconsequently\b",
        ]
        step_matches = sum(len(re.findall(p, full_text, re.IGNORECASE)) for p in step_patterns)
        step_by_step_clarity = min(100.0, step_matches * 12.0 + 40.0)
        logical_progression = min(100.0, step_matches * 10.0 + 45.0)

        # 3. Concept completeness (based on word count & explanation depth)
        word_count = len(full_text.split())
        concept_completeness = min(100.0, (word_count / 150.0) * 20.0 + 50.0)

        # 4. Redundancy & Coherence
        words = full_text.lower().split()
        unique_words = set(words)
        vocab_ratio = len(unique_words) / max(1, len(words))
        coherence_score = min(100.0, vocab_ratio * 120.0)
        redundancy_score = max(0.0, (1.0 - vocab_ratio) * 100.0)

        # Overall explanation score (100% deterministic)
        score = round(
            0.25 * definition_quality
            + 0.25 * step_by_step_clarity
            + 0.25 * logical_progression
            + 0.25 * concept_completeness,
            1,
        )

        strengths = []
        weaknesses = []

        if definition_quality >= 70:
            strengths.append("Clear formal definitions provided for key concepts.")
        else:
            weaknesses.append("Explicit concept definitions were limited.")

        if step_by_step_clarity >= 70:
            strengths.append("Good logical step-by-step progression with clear transition phrases.")
        else:
            weaknesses.append("Could improve step-by-step structural transitions between concepts.")

        if concept_completeness >= 70:
            strengths.append("Thorough depth and detailed conceptual explanation.")

        qualitative_summary = self._generate_gemini_reasoning(full_text, score, strengths, weaknesses)

        return {
            "score": score,
            "definition_quality": round(definition_quality, 1),
            "concept_completeness": round(concept_completeness, 1),
            "logical_progression": round(logical_progression, 1),
            "step_by_step_clarity": round(step_by_step_clarity, 1),
            "coherence_score": round(coherence_score, 1),
            "redundancy_score": round(redundancy_score, 1),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "qualitative_summary": qualitative_summary,
        }

    def _generate_gemini_reasoning(
        self, text_snippet: str, score: float, strengths: List[str], weaknesses: List[str]
    ) -> str:
        """Call Gemini 2.5 Flash for qualitative reasoning (with fallback)."""
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return (
                f"The faculty delivered an explanation scored at {score}/100. "
                f"Key strengths: {', '.join(strengths) if strengths else 'Standard clarity'}. "
                f"Areas for improvement: {', '.join(weaknesses) if weaknesses else 'None noted'}."
            )

        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = (
                f"You are a Senior Educational Quality Inspector evaluating a classroom lecture.\n"
                f"Explanation Score calculated deterministically: {score}/100.\n"
                f"Identified Strengths: {strengths}\n"
                f"Identified Weaknesses: {weaknesses}\n"
                f"Lecture Transcript Snippet: {text_snippet[:1000]}\n\n"
                f"Provide a 2-3 sentence professional qualitative assessment summarizing the clarity, "
                f"coherence, and pedagogical delivery of the explanation. Do not generate numeric scores."
            )
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            logger.warning("Gemini API call failed for explanation reasoning, using fallback: %s", e)

        return (
            f"The lecture explanation demonstrated a calculated quality score of {score}/100. "
            f"The delivery maintained structured progression and conceptual depth."
        )
