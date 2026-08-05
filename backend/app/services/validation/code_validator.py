"""
Code Validator component for Technical Validation Engine.
Detects code syntax errors, deprecated functions, wrong API calls, or logic issues in spoken/written code.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple
from app.services.validation.validation_models import ValidationType, SeverityLevel


class CodeValidator:
    """Validates code snippets or programming explanations inside transcript text."""

    @staticmethod
    def inspect_code(
        chunk_text: str,
        reference_text: str = "",
    ) -> Optional[Tuple[ValidationType, SeverityLevel, str, float]]:
        """
        Returns:
            (ValidationType, SeverityLevel, reason_explanation, confidence_score) or None if no code issue.
        """
        text_lower = chunk_text.lower()

        # Common programming misconceptions or invalid syntax patterns spoken/written
        code_patterns = [
            (
                r"\bprint\s+['\"][^'\"]+['\"]",
                "Python 3 requires print() function with parentheses: print('...'), not print '...'.",
            ),
            (
                r"\barray\.length\(\)",
                "In Java, array length is a property (.length), not a method call (.length()).",
            ),
            (
                r"\bstring\.length\b(?!\()",
                "In Java, String length is a method call (.length()), not a property (.length).",
            ),
            (
                r"\bmalloc\s*\(\s*sizeof\s*\(\s*int\s*\)\s*\)\s*;\s*free\s*\(\s*\w+\s*\)\s*;\s*\*\w+",
                "Use-after-free defect: Dereferencing pointer after calling free().",
            ),
            (
                r"\bconst\s+\w+\s*;|\blet\s+\w+\s*;",
                "Uninitialized constant declaration in code snippet.",
            ),
        ]

        for pattern, explanation in code_patterns:
            if re.search(pattern, chunk_text, re.IGNORECASE):
                return (
                    ValidationType.INCORRECT_CODE,
                    SeverityLevel.HIGH,
                    f"Code validation error: {explanation}",
                    91.0,
                )

        # Check explicit keywords indicating code explanations
        if any(kw in text_lower for kw in ["def ", "function", "return ", "class ", "import ", "public static void"]):
            # Check for return statement inside void function claim
            if "void" in text_lower and "return 0" in text_lower:
                return (
                    ValidationType.INCORRECT_CODE,
                    SeverityLevel.HIGH,
                    "Invalid Code Logic: A void function cannot return a value (e.g. return 0).",
                    88.0,
                )

        return None
