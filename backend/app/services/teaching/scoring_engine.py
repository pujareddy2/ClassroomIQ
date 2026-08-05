"""
Pedagogical Scoring Engine — Combines sub-scores with DB-configured dynamic weights.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class ScoringEngine:
    def calculate_overall_score(
        self,
        explanation_score: float,
        example_score: float,
        structure_score: float,
        interaction_score: float,
        coverage_score: float,
        validation_score: float,
        weights: Dict[str, float],
    ) -> Tuple[float, str]:
        """Calculates weighted average score (0-100) and assigns letter grade."""
        scores_map = {
            "Explanation": explanation_score,
            "Examples": example_score,
            "Structure": structure_score,
            "Interaction": interaction_score,
            "Coverage": coverage_score,
            "Validation": validation_score,
        }

        total_weighted_points = 0.0
        total_weight = 0.0

        for metric, score_val in scores_map.items():
            w = weights.get(metric, 0.0)
            total_weighted_points += score_val * w
            total_weight += w

        if total_weight <= 0.0:
            overall_score = 0.0
        else:
            overall_score = round(total_weighted_points / total_weight, 1)

        grade = self._assign_grade(overall_score)
        return overall_score, grade

    def _assign_grade(self, score: float) -> str:
        if score >= 90.0:
            return "A+"
        elif score >= 80.0:
            return "A"
        elif score >= 70.0:
            return "B"
        elif score >= 60.0:
            return "C"
        else:
            return "D"

    def calculate_confidence(
        self, has_transcript: bool, has_coverage: bool, has_validation: bool
    ) -> float:
        present_count = sum([has_transcript, has_coverage, has_validation])
        if present_count == 3:
            return 100.0
        elif present_count == 2:
            return 90.0
        elif present_count == 1:
            return 80.0
        else:
            return 60.0

    def consolidate_strengths_weaknesses(
        self,
        explanation_res: Dict,
        example_res: Dict,
        structure_res: Dict,
        interaction_res: Dict,
    ) -> Tuple[List[str], List[str]]:
        strengths: List[str] = []
        weaknesses: List[str] = []

        # Explanation
        strengths.extend(explanation_res.get("strengths", []))
        weaknesses.extend(explanation_res.get("weaknesses", []))

        # Examples
        ex_count = example_res.get("example_count", 0)
        if ex_count >= 2:
            strengths.append(f"Effective use of {ex_count} teaching examples across topics.")
        elif ex_count == 0:
            weaknesses.append("No practical or real-world examples were detected during explanation.")

        # Structure
        if structure_res.get("has_introduction") and structure_res.get("has_conclusion"):
            strengths.append("Well-structured lecture flow with clear introduction and summary.")
        elif not structure_res.get("has_introduction"):
            weaknesses.append("Missing explicit lecture introduction and agenda setting.")

        if structure_res.get("improper_ordering_count", 0) > 0:
            weaknesses.append("Detected erratic topic jumps disrupting conceptual continuity.")

        # Interaction
        if interaction_res.get("student_response_count", 0) > 0 or interaction_res.get("student_question_count", 0) > 0:
            strengths.append("Active student participation and classroom interaction.")
        else:
            weaknesses.append("Limited student engagement and interaction opportunities.")

        return strengths, weaknesses
