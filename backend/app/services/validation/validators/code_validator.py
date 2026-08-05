"""
Code Validator component.
Detects programming code syntax errors, deprecated APIs, or logic defects.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple
from app.services.validation.validation_models import (
    SeverityLevel,
    ValidationCategory,
    ValidationStatus,
    ValidationType,
)


class CodeValidator:
    """Validates code snippets or programming explanations inside transcript chunks."""

    @staticmethod
    def validate(
        chunk_text: str,
        reference_text: str = "",
    ) -> Optional[Tuple[ValidationCategory, ValidationStatus, ValidationType, SeverityLevel, str, float]]:
        text_lower = chunk_text.lower()

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
        ]

        for pattern, explanation in code_patterns:
            if re.search(pattern, chunk_text, re.IGNORECASE):
                return (
                    ValidationCategory.CODE,
                    ValidationStatus.INCORRECT,
                    ValidationType.INCORRECT_CODE,
                    SeverityLevel.HIGH,
                    f"Code validation error: {explanation}",
                    91.0,
                )

        if any(kw in text_lower for kw in ["def ", "function", "return ", "class ", "import ", "public static void"]):
            if "void" in text_lower and "return 0" in text_lower:
                return (
                    ValidationCategory.CODE,
                    ValidationStatus.INCORRECT,
                    ValidationType.INCORRECT_CODE,
                    SeverityLevel.HIGH,
                    "Invalid Code Logic: A void function cannot return a value (e.g. return 0).",
                    88.0,
                )

        return None
