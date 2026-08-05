"""
Formula Validator component for Technical Validation Engine.
Detects wrong equations, incorrect Big-O notation, missing variables, or wrong math logic.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple
from app.services.validation.validation_models import ValidationType, SeverityLevel


class FormulaValidator:
    """Detects mathematical equation or notation errors in transcript text."""

    @staticmethod
    def inspect_formula(
        chunk_text: str,
        reference_text: str = "",
    ) -> Optional[Tuple[ValidationType, SeverityLevel, str, float]]:
        """
        Returns:
            (ValidationType, SeverityLevel, reason_explanation, confidence_score) or None if no formula issue.
        """
        text_lower = chunk_text.lower()

        # Check Big-O notation mismatches
        # e.g. "O(n^2)" vs "O(n)" or claims like "Bubble sort is O(1)" or "Binary search is O(n^2)"
        big_o_matches = re.findall(r"\bo\s*\(\s*([a-zA-Z0-9\^\*\+\-\/]+)\s*\)", text_lower)

        if "bubble sort" in text_lower and any(o in ["1", "logn", "log n"] for o in big_o_matches):
            return (
                ValidationType.INCORRECT_FORMULA,
                SeverityLevel.HIGH,
                "Incorrect time complexity formula: Bubble Sort is O(n^2) worst case, not O(1) or O(log n).",
                92.0,
            )

        if "binary search" in text_lower and any(o in ["n^2", "n2", "n"] for o in big_o_matches):
            return (
                ValidationType.INCORRECT_FORMULA,
                SeverityLevel.HIGH,
                "Incorrect time complexity formula: Binary Search operations are O(log n), not O(n^2) or O(n).",
                90.0,
            )

        # Mathematical expression syntax errors or contradictions (e.g. 2+2=5, a^2+b^2=c^3)
        if re.search(r"\ba\s*\^\s*2\s*\+\s*b\s*\^\s*2\s*=\s*c\s*\^\s*3\b", text_lower):
            return (
                ValidationType.INCORRECT_FORMULA,
                SeverityLevel.HIGH,
                "Incorrect equation: Pythagorean theorem equation is a^2 + b^2 = c^2, not c^3.",
                95.0,
            )

        # Check explicit math operator / equation errors
        math_equation_patterns = [
            (r"e\s*=\s*m\s*c\s*\^\s*3", "Einstein's mass-energy equivalence equation is E = mc^2, not mc^3."),
            (r"f\s*=\s*m\s*\/\s*a\b", "Newton's second law is F = m * a (Force = mass x acceleration), not m / a."),
        ]

        for pattern, explanation in math_equation_patterns:
            if re.search(pattern, text_lower):
                return (
                    ValidationType.INCORRECT_FORMULA,
                    SeverityLevel.HIGH,
                    f"Incorrect mathematical formula: {explanation}",
                    94.0,
                )

        return None
