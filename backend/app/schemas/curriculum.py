from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

CurriculumDocumentType = str
ProcessingStatus = Literal["UPLOADED", "VALIDATED", "TEXT_EXTRACTED", "PARSED", "EMBEDDED", "READY"]


class CurriculumUploadMetadata(BaseModel):
    course_name: str = Field(min_length=2, max_length=255)
    academic_year: str = Field(min_length=9, max_length=9, pattern=r"^\d{4}-\d{4}$")
    semester: str = Field(min_length=1, max_length=50)
    faculty_name: str = Field(min_length=2, max_length=255)
    title: str = Field(min_length=2, max_length=255)
    document_type: CurriculumDocumentType = "SYLLABUS"
    description: str | None = Field(default=None, max_length=1000)


# ── Structured curriculum response models ──────────────────────────────────────

class ChapterSchema(BaseModel):
    """A chapter / section inside a unit."""
    title: str
    topics: list[str] = Field(default_factory=list)


class UnitSchema(BaseModel):
    """A single unit / module of the syllabus."""
    unit_number: int
    title: str
    chapters: list[ChapterSchema] = Field(default_factory=list)
    learning_outcomes: list[str] = Field(default_factory=list)


class ParsedCurriculumSchema(BaseModel):
    """The fully parsed curriculum tree returned after upload."""
    title: str
    course_id: UUID
    units: list[UnitSchema] = Field(default_factory=list)


class CurriculumUploadResponse(BaseModel):
    status: str
    message: str
    document_id: UUID
    course_id: UUID
    processing_status: ProcessingStatus
    uploaded_at: datetime
    # Structured curriculum tree (primary output)
    curriculum: ParsedCurriculumSchema | None = None
    # Raw text and metadata kept for debugging / downstream use
    extracted_text: str | None = None
    extraction_metadata: dict[str, Any] | None = None


class CurriculumRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    faculty_id: UUID
    title: str
    document_type: str
    file_name: str
    file_path: str
    file_size: int
    processing_status: str
    uploaded_at: datetime


class CurriculumListItem(BaseModel):
    """Lightweight curriculum record for list/search responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    faculty_id: UUID
    title: str
    document_type: str
    file_name: str
    processing_status: str
    uploaded_at: datetime
    description: str | None = None


class CurriculumDeleteResponse(BaseModel):
    """Response returned after a successful soft-delete of a curriculum."""
    curriculum_id: UUID
    status: str = "DELETED"
    message: str = "Curriculum soft-deleted successfully."
