"""
Terminology & Definition Validator component.
Detects definition mistakes, terminology confusion, or outdated academic terms.
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


class TerminologyValidator:
    """Validates academic terminology and definitions."""

    @staticmethod
    def validate(
        chunk_text: str,
        reference_text: str = "",
    ) -> Optional[Tuple[ValidationCategory, ValidationStatus, ValidationType, SeverityLevel, str, float]]:
        text_lower = chunk_text.lower()

        patterns = [
            (
                r"\bstack\s+is\s+a\s+fifo\b|\bqueue\s+is\s+a\s+lifo\b",
                ValidationCategory.TERMINOLOGY,
                ValidationStatus.INCORRECT,
                ValidationType.TERMINOLOGY_ERROR,
                SeverityLevel.HIGH,
                "Terminology mismatch: Stack is LIFO (Last-In-First-Out); Queue is FIFO (First-In-First-Out).",
                93.0,
            ),
            (
                r"\bhttp\s+is\s+a\s+stateful\b",
                ValidationCategory.DEFINITION,
                ValidationStatus.INCORRECT,
                ValidationType.OUTDATED_DEFINITION,
                SeverityLevel.MEDIUM,
                "Definition error: HTTP is fundamentally a stateless application layer protocol.",
                88.0,
            ),
        ]

        for pattern, cat, status, v_type, severity, explanation, score in patterns:
            if re.search(pattern, text_lower):
                return cat, status, v_type, severity, explanation, score

        return None
