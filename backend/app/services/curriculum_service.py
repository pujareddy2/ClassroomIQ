from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.curriculum import Curriculum
from app.repositories.curriculum_repository import CurriculumRepository
from app.schemas.curriculum import CurriculumUploadMetadata, CurriculumUploadResponse
from app.services.document_extractor.service import DocumentExtractionService
from app.utils.config import settings
from app.utils.file_validation import (
    ALLOWED_SYLLABUS_TYPES,
    MissingMetadataError,
    normalize_semester,
    parse_academic_year_dates,
    validate_document_type,
    validate_file_extension,
    validate_file_size,
)
from app.utils.storage import build_document_directory, save_document_bytes

PROCESSING_STATUS_UPLOADED = "UPLOADED"


class CurriculumService:
    def __init__(self, db: Session) -> None:
        self.repository = CurriculumRepository(db)

    async def upload_curriculum(self, metadata: CurriculumUploadMetadata, upload_file: UploadFile) -> tuple[Curriculum, CurriculumUploadResponse]:
        if not metadata.title.strip():
            raise MissingMetadataError("Title is required")

        faculty = self.repository.get_faculty_by_name(metadata.faculty_name)
        if faculty is None:
            raise LookupError(f"Faculty '{metadata.faculty_name}' not found")

        course = self.repository.get_course_by_selector(metadata.course_name)
        if course is None:
            normalized_code = metadata.course_name.strip().upper().replace(" ", "_")[:50]
            course = self.repository.create_course(normalized_code, metadata.course_name.strip(), faculty.department_id)

        semester_number = normalize_semester(metadata.semester)
        start_date, end_date = parse_academic_year_dates(metadata.academic_year)
        academic_term = self.repository.get_or_create_academic_term(
            institution_id=faculty.department.institution_id,
            academic_year=metadata.academic_year.strip(),
            semester=semester_number,
            start_date=start_date,
            end_date=end_date,
        )

        document_type = validate_document_type(metadata.document_type, ALLOWED_SYLLABUS_TYPES)
        file_extension = validate_file_extension(upload_file.filename or "")

        if document_type != "SYLLABUS":
            raise ValueError("Curriculum uploads must use document_type=SYLLABUS")

        content = await upload_file.read(settings.max_file_size_bytes + 1)
        validate_file_size(len(content), settings.max_file_size_bytes)

        directory = build_document_directory(course.course_name, academic_term.academic_year, str(metadata.semester), document_type)
        saved_path = save_document_bytes(directory, upload_file.filename or f"curriculum{file_extension}", content)

        next_version = self.repository.count_curricula_for_course_term(course.id, academic_term.id) + 1
        curriculum = Curriculum(
            course_id=course.id,
            academic_term_id=academic_term.id,
            faculty_id=faculty.id,
            title=metadata.title.strip(),
            document_type=document_type,
            description=metadata.description.strip() if metadata.description else None,
            file_name=saved_path.name,
            file_path=str(saved_path),
            file_size=len(content),
            mime_type=upload_file.content_type or "application/octet-stream",
            syllabus_version=f"v{next_version}",
            processing_status=PROCESSING_STATUS_UPLOADED,
        )

        try:
            created = self.repository.create_curriculum(curriculum)
        except Exception:
            if saved_path.exists():
                saved_path.unlink(missing_ok=True)
            self.repository.db.rollback()
            raise

        extraction_service = DocumentExtractionService(self.repository.db)
        extracted = extraction_service.extract_text_from_path(saved_path)
        extraction_service.update_document_record(created, extracted)

        response = CurriculumUploadResponse(
            status="success",
            message="Curriculum uploaded successfully",
            document_id=created.id,
            course_id=created.course_id,
            processing_status=created.processing_status,
            uploaded_at=created.uploaded_at,
            extracted_text=extracted.text,
            metadata=extracted.metadata,
        )
        return created, response
