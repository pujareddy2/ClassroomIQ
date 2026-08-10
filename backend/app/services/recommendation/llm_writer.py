"""
Module 3: LLM Recommendation Writer

Uses Gemini 2.5 Flash to rewrite deterministic recommendations into professional,
faculty-friendly pedagogical feedback.

IMPORTANT: The LLM does NOT decide recommendations — it only rewrites title,
reason, and recommended_action using concise, constructive phrasing.
"""

import logging
import os
from typing import List

from app.services.recommendation.evidence_collector import EvidenceBundle
from app.services.recommendation.rule_engine import RawRecommendation

logger = logging.getLogger(__name__)


class LLMRecommendationWriter:

    def rewrite_recommendations(
        self, raw_recs: List[RawRecommendation], bundle: EvidenceBundle
    ) -> List[RawRecommendation]:
        """Rewrite raw recommendations using Gemini 2.5 Flash (with fallback)."""
        if not raw_recs:
            return []

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            logger.info("GEMINI_API_KEY not found; using deterministic rule text directly.")
            return raw_recs

        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")

            # Prepare concise input summary — NEVER send entire transcript or PDF text
            evidence_summary = [
                f"- [{f.source.upper()}] {f.evidence_type}: {f.description}"
                for f in (bundle.coverage_facts + bundle.validation_facts + bundle.teaching_facts)[:8]
            ]
            evidence_str = "\n".join(evidence_summary) or "No critical weaknesses detected."

            items_to_rewrite = []
            for i, r in enumerate(raw_recs):
                items_to_rewrite.append(
                    f"Item {i+1}:\n"
                    f"  Category: {r.category}\n"
                    f"  Type: {r.recommendation_type}\n"
                    f"  Current Title: {r.title}\n"
                    f"  Raw Reason: {r.reason}\n"
                    f"  Raw Action: {r.recommended_action}\n"
                )
            items_str = "\n".join(items_to_rewrite)

            prompt = (
                f"You are a Senior Educational Quality Inspector and Faculty Development Specialist.\n"
                f"Below is a list of deterministic recommendations calculated for a college lecture based on empirical data.\n\n"
                f"EVIDENCE SUMMARY:\n{evidence_str}\n\n"
                f"RAW RECOMMENDATIONS TO REWRITE:\n{items_str}\n\n"
                f"INSTRUCTIONS:\n"
                f"1. DO NOT add or remove recommendations. Keep exact same count ({len(raw_recs)}).\n"
                f"2. DO NOT change categories or numeric priority scores.\n"
                f"3. For each Item, rewrite 'Title', 'Reason', and 'Recommended Action' to be professional, encouraging, constructive, and actionable.\n"
                f"4. Output format for each item:\n"
                f"ITEM <N>\n"
                f"Title: <rewritten title>\n"
                f"Reason: <rewritten reason>\n"
                f"Action: <rewritten recommended action>\n"
            )

            response = model.generate_content(prompt)
            if response and response.text:
                self._parse_and_apply_llm_response(raw_recs, response.text)

        except Exception as e:
            logger.warning("Gemini LLM recommendation rewrite failed: %s; keeping raw rule text", e)

        return raw_recs

    def _parse_and_apply_llm_response(
        self, raw_recs: List[RawRecommendation], llm_text: str
    ):
        """Parse structured LLM response block and update raw_recs in-place."""
        import re

        blocks = re.split(r"ITEM\s+\d+", llm_text, flags=re.IGNORECASE)
        blocks = [b.strip() for b in blocks if b.strip()]

        for i, block in enumerate(blocks):
            if i >= len(raw_recs):
                break

            title_m = re.search(r"Title:\s*(.+)", block, re.IGNORECASE)
            reason_m = re.search(r"Reason:\s*(.+)", block, re.IGNORECASE)
            action_m = re.search(r"Action:\s*(.+)", block, re.IGNORECASE)

            if title_m and title_m.group(1).strip():
                raw_recs[i].title = title_m.group(1).strip()
            if reason_m and reason_m.group(1).strip():
                raw_recs[i].reason = reason_m.group(1).strip()
            if action_m and action_m.group(1).strip():
                raw_recs[i].recommended_action = action_m.group(1).strip()
