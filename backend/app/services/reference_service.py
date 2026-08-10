from __future__ import annotations

import logging
from typing import Any

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.reference_material import ReferenceMaterial
from app.repositories.reference_repository import ReferenceRepository
from app.schemas.reference_material import ReferenceUploadMetadata, ReferenceUploadResponse
from app.services.document_extractor.service import DocumentExtractionService
from app.utils.config import settings
from app.utils.file_validation import (
    ALLOWED_REFERENCE_TYPES,
    MissingMetadataError,
    normalize_semester,
    parse_academic_year_dates,
    validate_document_type,
    validate_file_extension,
    validate_file_size,
)
from app.utils.storage import build_document_directory, save_document_bytes

logger = logging.getLogger(__name__)
PROCESSING_STATUS_UPLOADED = "UPLOADED"


class ReferenceService:
    def __init__(self, db: Session) -> None:
        self.repository = ReferenceRepository(db)

    async def upload_reference_material(
        self,
        metadata: ReferenceUploadMetadata,
        upload_file: UploadFile,
    ) -> tuple[ReferenceMaterial, ReferenceUploadResponse]:
        if not metadata.title.strip():
            raise MissingMetadataError("Title is required")

        # ── Resolve faculty ────────────────────────────────────────────────
        faculty = self.repository.get_faculty_by_name(metadata.faculty_name)
        if faculty is None:
            raise LookupError(f"Faculty '{metadata.faculty_name}' not found")

        # ── Resolve or create course ───────────────────────────────────────
        course = self.repository.get_course_by_selector(metadata.course_name)
        if course is None:
            normalized_code = metadata.course_name.strip().upper().replace(" ", "_")[:50]
            course = self.repository.create_course(
                normalized_code, metadata.course_name.strip(), faculty.department_id
            )

        # ── Resolve or create academic term ───────────────────────────────
        semester_number = normalize_semester(metadata.semester)
        start_date, end_date = parse_academic_year_dates(metadata.academic_year)
        academic_term = self.repository.get_or_create_academic_term(
            institution_id=faculty.department.institution_id,
            academic_year=metadata.academic_year.strip(),
            semester=semester_number,
            start_date=start_date,
            end_date=end_date,
        )

        # ── Validate file ──────────────────────────────────────────────────
        document_type = validate_document_type(metadata.document_type, ALLOWED_REFERENCE_TYPES)
        file_extension = validate_file_extension(upload_file.filename or "")

        content = await upload_file.read(settings.max_file_size_bytes + 1)
        validate_file_size(len(content), settings.max_file_size_bytes)

        # ── Save file to disk ──────────────────────────────────────────────
        directory = build_document_directory(
            course.course_name,
            academic_term.academic_year,
            str(metadata.semester),
            document_type,
        )
        saved_path = save_document_bytes(
            directory,
            upload_file.filename or f"reference_document{file_extension}",
            content,
        )

        # ── Persist record ─────────────────────────────────────────────────
        reference_material = ReferenceMaterial(
            course_id=course.id,
            faculty_id=faculty.id,
            academic_term_id=academic_term.id,
            title=metadata.title.strip(),
            document_type=document_type,
            description=metadata.description.strip() if metadata.description else None,
            file_name=saved_path.name,
            file_path=str(saved_path),
            file_size=len(content),
            mime_type=upload_file.content_type or "application/octet-stream",
            processing_status=PROCESSING_STATUS_UPLOADED,
        )

        try:
            created = self.repository.create_reference_material(reference_material)
        except Exception:
            if saved_path.exists():
                saved_path.unlink(missing_ok=True)
            self.repository.db.rollback()
            raise

        # ── Extract text (non-fatal) ───────────────────────────────────────
        extracted_text: str | None = None
        extraction_metadata: dict[str, Any] | None = None
        try:
            extraction_service = DocumentExtractionService(self.repository.db)
            extracted = extraction_service.extract_text_from_path(saved_path)
            # Only update processing_status — avoid touching missing ORM columns
            created.processing_status = "TEXT_EXTRACTED"
            self.repository.db.add(created)
            self.repository.db.flush()
            extracted_text = extracted.text
            extraction_metadata = extracted.metadata
        except Exception as exc:
            logger.warning("Text extraction failed for reference material: %s", exc)
            # Non-fatal — record stays in UPLOADED status

        response = ReferenceUploadResponse(
            status="success",
            message="Reference material uploaded successfully",
            document_id=created.id,
            course_id=created.course_id,
            processing_status=created.processing_status,
            uploaded_at=created.created_at,
            extracted_text=extracted_text,
            extraction_metadata=extraction_metadata,
        )
        return created, response
