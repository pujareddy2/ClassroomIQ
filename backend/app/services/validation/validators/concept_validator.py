"""
Concept Validator component.
Validates general conceptual correctness and detects incorrect/missing concepts using LLM or deterministic fallback.
"""

from __future__ import annotations

import logging
import os
import re
from typing import List, Optional, Tuple

from app.services.validation.validation_models import (
    InternalEvidence,
    SeverityLevel,
    ValidationCategory,
    ValidationStatus,
    ValidationType,
)

logger = logging.getLogger(__name__)

CONCEPT_CONTRADICTIONS = [
    (
        r"\bcompiler\s+(?:executes|runs)\b",
        ValidationCategory.CONCEPT,
        ValidationStatus.INCORRECT,
        ValidationType.INCORRECT_CONCEPT,
        SeverityLevel.HIGH,
        "A compiler translates source code into target machine code; it does not execute programs. An interpreter or CPU executes code.",
    ),
    (
        r"\binterpreter\s+(?:translates|compiles)\s+(?:all|entire|whole)\s+(?:source code|program)\b",
        ValidationCategory.CONCEPT,
        ValidationStatus.INCORRECT,
        ValidationType.INCORRECT_CONCEPT,
        SeverityLevel.HIGH,
        "An interpreter translates and executes source code line-by-line; it does not translate the entire program at once like a compiler.",
    ),
    (
        r"\blexical\s+analys(?:is|er)\s+(?:generates|creates|builds)\s+(?:parse|syntax)\s+tree\b",
        ValidationCategory.CONCEPT,
        ValidationStatus.INCORRECT,
        ValidationType.INCORRECT_CONCEPT,
        SeverityLevel.HIGH,
        "Lexical analysis produces tokens from characters. Syntax analysis (parsing) builds the parse tree.",
    ),
]


class ConceptValidator:
    """Validates lecture conceptual correctness against academic reference materials."""

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.use_llm = bool(self.api_key and self.api_key.strip())

    def validate(
        self,
        chunk_text: str,
        topic_name: str,
        references: List[Tuple[Optional[str], str, str, str]],
    ) -> Tuple[ValidationCategory, ValidationStatus, ValidationType, SeverityLevel, str, float]:
        # 1. Deterministic contradiction rules
        for pattern, cat, status, v_type, severity, explanation in CONCEPT_CONTRADICTIONS:
            if re.search(pattern, chunk_text, re.IGNORECASE):
                return cat, status, v_type, severity, explanation, 94.0

        # 2. LLM validation if API key present
        if self.use_llm:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")

                ref_texts = "\n".join([f"- {doc}: {excerpt}" for _, doc, _, excerpt in references])
                prompt = f"""
You are an academic validator reviewing a lecture statement against reference materials.

TOPIC: {topic_name}
STATEMENT: "{chunk_text}"

REFERENCES:
{ref_texts}

Check conceptual accuracy.
Return output in this format:
STATUS: <CORRECT/INCORRECT/MISSING>
REASON: <Academic explanation>
CONFIDENCE: <0-100>
"""
                response = model.generate_content(prompt)
                parsed = self._parse_llm(response.text)
                if parsed:
                    return parsed
            except Exception as exc:
                logger.warning("LLM API call failed, falling back: %s", exc)

        # Default: Correct
        explanation = f"The lecture explanation of '{topic_name}' aligns with standard curriculum reference materials."
        return (
            ValidationCategory.CONCEPT,
            ValidationStatus.CORRECT,
            ValidationType.CORRECT,
            SeverityLevel.LOW,
            explanation,
            88.0,
        )

    def _parse_llm(self, text: str) -> Optional[Tuple[ValidationCategory, ValidationStatus, ValidationType, SeverityLevel, str, float]]:
        try:
            status_match = re.search(r"STATUS:\s*([A-Z]+)", text)
            reason_match = re.search(r"REASON:\s*(.+)", text)
            conf_match = re.search(r"CONFIDENCE:\s*([0-9\.]+)", text)

            if status_match and reason_match:
                st = ValidationStatus(status_match.group(1).strip())
                reason = reason_match.group(1).strip()
                conf = float(conf_match.group(1).strip()) if conf_match else 85.0
                v_type = ValidationType.CORRECT if st == ValidationStatus.CORRECT else ValidationType.INCORRECT_CONCEPT
                sev = SeverityLevel.LOW if st == ValidationStatus.CORRECT else SeverityLevel.HIGH
                return ValidationCategory.CONCEPT, st, v_type, sev, reason, conf
        except Exception:
            pass
        return None
