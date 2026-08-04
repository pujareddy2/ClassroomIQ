from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ReferenceDocumentType = Literal["REFERENCE_BOOK", "FACULTY_NOTES", "PPT", "LAB_MANUAL", "ASSIGNMENT", "QUESTION_BANK"]
ProcessingStatus = Literal["UPLOADED", "VALIDATED", "TEXT_EXTRACTED", "PARSED", "EMBEDDED", "READY"]


class ReferenceUploadMetadata(BaseModel):
    course_name: str = Field(min_length=2, max_length=255)
    academic_year: str = Field(min_length=9, max_length=9, pattern=r"^\d{4}-\d{4}$")
    semester: str = Field(min_length=1, max_length=50)
    faculty_name: str = Field(min_length=2, max_length=255)
    title: str = Field(min_length=2, max_length=255)
    document_type: ReferenceDocumentType
    description: str | None = Field(default=None, max_length=1000)


class ReferenceUploadResponse(BaseModel):
    status: str
    message: str
    document_id: UUID
    course_id: UUID
    processing_status: ProcessingStatus
    uploaded_at: datetime
    extracted_text: str | None = None
    metadata: dict[str, object] | None = None


class ReferenceRecord(BaseModel):
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
    created_at: datetime
