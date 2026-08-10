"""
Internal models for the Technical Validation Engine pipeline.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ValidationCategory(str, Enum):
    CONCEPT = "CONCEPT"
    FORMULA = "FORMULA"
    CODE = "CODE"
    TERMINOLOGY = "TERMINOLOGY"
    DEFINITION = "DEFINITION"
    ALGORITHM = "ALGORITHM"
    EXAMPLE = "EXAMPLE"


class ValidationStatus(str, Enum):
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    MISSING = "MISSING"


class ValidationType(str, Enum):
    CORRECT = "CORRECT"
    INCORRECT_CONCEPT = "INCORRECT_CONCEPT"
    INCORRECT_FORMULA = "INCORRECT_FORMULA"
    INCORRECT_CODE = "INCORRECT_CODE"
    MISSING_CONCEPT = "MISSING_CONCEPT"
    OUTDATED_DEFINITION = "OUTDATED_DEFINITION"
    TERMINOLOGY_ERROR = "TERMINOLOGY_ERROR"


class SeverityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class InternalEvidence(BaseModel):
    reference_material_id: Optional[UUID] = None
    reference_document: str
    reference_section: Optional[str] = None
    reference_excerpt: str
    curriculum_topic: str
    explanation: str


class ValidationChunkResult(BaseModel):
    chunk_id: str
    chunk_text: str
    chunk_start_time: float
    chunk_end_time: float
    speaker: str
    topic_id: Optional[UUID] = None
    topic_name: str = "General"
    category: ValidationCategory = ValidationCategory.CONCEPT
    status: ValidationStatus = ValidationStatus.CORRECT
    validation_type: ValidationType = ValidationType.CORRECT
    severity: SeverityLevel = SeverityLevel.LOW
    confidence_score: float = 85.0
    confidence_level: SeverityLevel = SeverityLevel.HIGH
    reason: str
    evidence: List[InternalEvidence] = Field(default_factory=list)
