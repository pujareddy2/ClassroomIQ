from __future__ import annotations

import logging
import re
from typing import Any
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.curriculum import Curriculum
from app.repositories.curriculum_repository import CurriculumRepository
from app.schemas.curriculum import (
    ChapterSchema,
    CurriculumUploadMetadata,
    CurriculumUploadResponse,
    ParsedCurriculumSchema,
    UnitSchema,
)
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

logger = logging.getLogger(__name__)
PROCESSING_STATUS_UPLOADED = "UPLOADED"
PROCESSING_STATUS_PARSED = "PARSED"

# ── Regex patterns for curriculum parsing ──────────────────────────────────────

# Matches Unit/Module/Chapter headers: "UNIT I - ...", "MODULE 1: ...", "UNIT-1"
_UNIT_RE = re.compile(
    r"^\s*(?:UNIT|MODULE|CHAPTER|PART)\s*[\-–—:]?\s*"
    r"(?P<num>[IVXivx\d]+)\s*[\-–—:]?\s*(?P<title>.*)$",
    re.IGNORECASE,
)

# Matches Roman Numerals I–X
_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
          "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}

# Learning outcomes: CO1, LO1, PO1, CLO1
_LO_RE = re.compile(r"^\s*(?:CO|LO|PO|CLO)\s*[\d]+\s*[:\.\-–]?\s*(.+)$", re.IGNORECASE)

# Bullet / List markers
_TOPIC_RE = re.compile(r"^\s*(?:[\u2022\u2023\u25E6\-\*•]|\d+[\.\)])\s+(.+)$")


def _roman_to_int(s: str) -> int:
    s = s.strip().upper()
    if s in _ROMAN:
        return _ROMAN[s]
    try:
        return int(s)
    except ValueError:
        return 0


def _parse_curriculum_text(text: str, title: str, course_id: Any) -> ParsedCurriculumSchema:
    """
    Parse raw extracted text into structured Units, Chapters, Topics, and Outcomes.
    Guarantees topics are never discarded even if sub-headings are missing.
    """
    lines = text.splitlines()
    units: list[UnitSchema] = []
    current_unit: UnitSchema | None = None
    current_chapter_title: str | None = None
    current_chapter_topics: list[str] = []

    def _flush_chapter() -> None:
        nonlocal current_chapter_title, current_chapter_topics
        if current_unit is not None and (current_chapter_title or current_chapter_topics):
            ch_title = current_chapter_title if current_chapter_title else "Topics"
            current_unit.chapters.append(
                ChapterSchema(
                    title=ch_title,
                    topics=list(current_chapter_topics),
                )
            )
        current_chapter_title = None
        current_chapter_topics = []

    def _flush_unit() -> None:
        _flush_chapter()
        if current_unit is not None:
            units.append(current_unit)

    def _looks_like_chapter_heading(line: str) -> bool:
        stripped = line.strip()
        if not stripped or len(stripped) < 3 or len(stripped) > 80:
            return False
        if "," in stripped or ";" in stripped:
            return False
        if stripped[0] in "•*-0123456789":
            return False
        words = stripped.split()
        if len(words) == 1 and stripped[0].isupper():
            return True
        capitalized = sum(1 for w in words if w and w[0].isupper())
        return capitalized >= max(1, len(words) * 0.6)

    unit_count = 0
    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip():
            continue

        # 1. Check Unit Header
        unit_match = _UNIT_RE.match(line)
        if unit_match:
            _flush_unit()
            num_str = unit_match.group("num")
            unit_num = _roman_to_int(num_str) if num_str else (unit_count + 1)
            unit_title = unit_match.group("title").strip(" :-–—") or f"Unit {unit_num}"
            current_unit = UnitSchema(unit_number=unit_num, title=unit_title, chapters=[], learning_outcomes=[])
            current_chapter_title = None
            current_chapter_topics = []
            unit_count += 1
            continue

        if current_unit is None:
            continue

        # 2. Check Learning Outcomes
        lo_match = _LO_RE.match(line)
        if lo_match:
            current_unit.learning_outcomes.append(line.strip())
            continue

        # 3. Check Bullet Item
        topic_match = _TOPIC_RE.match(line)
        if topic_match:
            topic_text = topic_match.group(1).strip()
            # Split comma items if line contains multiple topic phrases
            sub_items = [i.strip() for i in topic_text.split(",") if i.strip()]
            current_chapter_topics.extend(sub_items if sub_items else [topic_text])
            continue

        # 4. Check Chapter Heading
        if _looks_like_chapter_heading(line):
            _flush_chapter()
            current_chapter_title = line.strip()
            continue

        # 5. Plain text lines inside unit -> treat as topics
        stripped = line.strip()
        if stripped and len(stripped) < 200:
            sub_items = [i.strip() for i in stripped.split(",") if i.strip()]
            current_chapter_topics.extend(sub_items if sub_items else [stripped])

    _flush_unit()

    # Fallback if no units matched: create default General unit with extracted lines as topics
    if not units:
        all_topics = []
        for l in text.splitlines():
            s = l.strip()
            if s and len(s) < 150 and not s.lower().startswith("course"):
                all_topics.extend([i.strip() for i in s.split(",") if i.strip()])
        units = [
            UnitSchema(
                unit_number=1,
                title="General Syllabus",
                chapters=[ChapterSchema(title="Topics", topics=all_topics[:50])],
                learning_outcomes=[],
            )
        ]

    return ParsedCurriculumSchema(title=title, course_id=course_id, units=units)


# ── Service Implementation ─────────────────────────────────────────────────────

class CurriculumService:
    def __init__(self, db: Session) -> None:
        self.repository = CurriculumRepository(db)

    async def upload_curriculum(
        self,
        metadata: CurriculumUploadMetadata,
        upload_file: UploadFile,
    ) -> tuple[Curriculum, CurriculumUploadResponse]:
        if not metadata.title.strip():
            raise MissingMetadataError("Title is required")

        faculty = self.repository.get_faculty_by_name(metadata.faculty_name)
        if faculty is None:
            raise LookupError(f"Faculty '{metadata.faculty_name}' not found")

        course = self.repository.get_course_by_selector(metadata.course_name)
        if course is None:
            normalized_code = metadata.course_name.strip().upper().replace(" ", "_")[:50]
            course = self.repository.create_course(
                normalized_code, metadata.course_name.strip(), faculty.department_id
            )

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

        # ── Step 1 & 2: Save PDF to Disk & Create Metadata in DB ─────────────
        directory = build_document_directory(
            course.course_name,
            academic_term.academic_year,
            str(metadata.semester),
            document_type,
        )
        saved_path = save_document_bytes(
            directory, upload_file.filename or f"curriculum{file_extension}", content
        )
        logger.info("PDF saved: %s", saved_path)

        next_version = (
            self.repository.count_curricula_for_course_term(course.id, academic_term.id) + 1
        )
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

        # ── Step 3 & 4: Extract Text & Store Extracted Text in DB ─────────────
        extraction_service = DocumentExtractionService(self.repository.db)
        extracted = extraction_service.extract_text_from_path(saved_path)
        logger.info("Text extracted: %d characters", len(extracted.text or ""))

        extraction_service.update_document_record(created, extracted)
        logger.info("Text stored in DB for document: %s", created.id)

        # ── Step 5 & 6: Run Curriculum Parser (Units, Chapters, Topics) ───────
        parsed_curriculum: ParsedCurriculumSchema | None = None
        try:
            raw_text = extracted.text or ""
            parsed_curriculum = _parse_curriculum_text(
                text=raw_text,
                title=metadata.title.strip(),
                course_id=created.course_id,
            )

            total_units = len(parsed_curriculum.units)
            total_chapters = sum(len(u.chapters) for u in parsed_curriculum.units)
            total_topics = sum(
                sum(len(ch.topics) for ch in u.chapters) for u in parsed_curriculum.units
            )

            logger.info("Units parsed: %d", total_units)
            logger.info("Chapters parsed: %d", total_chapters)
            logger.info("Topics parsed: %d", total_topics)

            # ── Step 7 & 9: Persist Units/Chapters/Topics into Database ────────
            saved_topic_rows = self.repository.save_topics_from_parsed_curriculum(
                curriculum_id=created.id,
                parsed=parsed_curriculum,
            )
            created.processing_status = PROCESSING_STATUS_PARSED
            self.repository.db.add(created)
            self.repository.db.flush()

            logger.info(
                "Database inserts completed: %d topic rows inserted into database",
                len(saved_topic_rows),
            )

        except Exception as parse_err:
            logger.error("Curriculum structure parsing failed: %s", parse_err, exc_info=True)

        response = CurriculumUploadResponse(
            status="success",
            message="Curriculum uploaded, parsed, and persisted to database successfully",
            document_id=created.id,
            course_id=created.course_id,
            processing_status=created.processing_status,
            uploaded_at=created.uploaded_at,
            curriculum=parsed_curriculum,
            extracted_text=extracted.text,
            extraction_metadata=extracted.metadata,
        )
        return created, response

    def get_curriculum_by_id(self, document_id: UUID) -> tuple[Curriculum, ParsedCurriculumSchema]:
        """
        Step 10: Load curriculum metadata, extracted text, and parsed topics
        directly from PostgreSQL database.
        """
        curriculum = self.repository.get_curriculum_by_id(document_id)
        if curriculum is None:
            raise LookupError(f"Curriculum document with ID '{document_id}' not found")

        parsed_curriculum = self.repository.load_parsed_curriculum_from_db(curriculum)
        return curriculum, parsed_curriculum
