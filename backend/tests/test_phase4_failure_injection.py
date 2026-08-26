"""
Failure Injection Test Suite for Phase 4.
Tests intentional failures and boundary conditions:
- Empty reference document
- Missing reference file on disk
- Non-existent course ID during retrieval
- Empty transcript chunks for analysis
- Non-existent lecture session ID
- Attempting analysis on lecture without transcript
- Course data isolation boundaries
"""

from __future__ import annotations

import pytest
import uuid
from pathlib import Path
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.reference_material import ReferenceMaterial
from app.models.lecture_session import LectureSession
from app.models.curriculum import Curriculum
from app.models.course import Course
from app.models.department import Department
from app.models.institution import Institution
from app.services.rag.rag_retrieval_service import RAGRetrievalService
from app.services.document_extractor.service import DocumentExtractionService
from app.services.document_extractor.exceptions import EmptyDocumentError
from app.services.analysis_execution_service import AnalysisExecutionService, run_analysis_job
from app.services.validation.validation_service import ValidationService
from app.services.validation.exceptions import EmptyTranscriptError


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_empty_document_extraction_failure(tmp_path: Path):
    """Empty document file should raise EmptyDocumentError gracefully."""
    empty_file = tmp_path / "empty_doc.txt"
    empty_file.write_text("", encoding="utf-8")
    
    extractor = DocumentExtractionService()
    with pytest.raises(EmptyDocumentError):
        extractor.extract_text_from_path(empty_file)


def test_missing_file_extraction_failure(tmp_path: Path):
    """Non-existent file path should raise FileNotFoundError."""
    missing_file = tmp_path / "does_not_exist.pdf"
    extractor = DocumentExtractionService()
    with pytest.raises(FileNotFoundError):
        extractor.extract_text_from_path(missing_file)


def test_nonexistent_reference_indexing_failure(db_session):
    """Indexing a non-existent reference material ID should raise LookupError."""
    rag_service = RAGRetrievalService(db_session)
    fake_id = uuid.uuid4()
    with pytest.raises(LookupError):
        rag_service.index_reference_material(fake_id)


def test_empty_transcript_validation_failure(db_session):
    """ValidationService should raise EmptyTranscriptError when empty chunk list is passed."""
    val_service = ValidationService(db_session)
    with pytest.raises(EmptyTranscriptError):
        val_service.process_and_validate_transcript([])


def test_analysis_job_without_lecture_failure(db_session):
    """AnalysisExecutionService should raise LookupError for non-existent lecture."""
    exec_service = AnalysisExecutionService(db_session)
    fake_lecture_id = uuid.uuid4()
    fake_curriculum_id = uuid.uuid4()
    with pytest.raises(LookupError):
        exec_service.start(lecture_id=fake_lecture_id, curriculum_id=fake_curriculum_id)


def test_analysis_run_without_transcript_chunks(db_session):
    """run_analysis_job should fail gracefully if lecture has no transcript chunks."""
    from datetime import date
    from app.models.academic_term import AcademicTerm
    from app.models.user import User
    from app.models.faculty import Faculty

    inst = Institution(id=uuid.uuid4(), name="Test Inst", contact_email=f"test_{uuid.uuid4().hex[:6]}@inst.edu")
    dept = Department(id=uuid.uuid4(), institution_id=inst.id, code="TEST_DEPT", name="Test Dept")
    user = User(id=uuid.uuid4(), full_name="Test Faculty", email=f"fac_{uuid.uuid4().hex[:6]}@test.edu", password_hash="hash", role="faculty")
    faculty = Faculty(id=uuid.uuid4(), user_id=user.id, department_id=dept.id, employee_id=f"EMP_{uuid.uuid4().hex[:6]}")
    term = AcademicTerm(id=uuid.uuid4(), institution_id=inst.id, academic_year="2026-2027", semester="Fall 2026", start_date=date(2026,8,1), end_date=date(2026,12,31))
    crs = Course(
        id=uuid.uuid4(),
        department_id=dept.id,
        course_code=f"TEST_{uuid.uuid4().hex[:6]}",
        course_name="Test Course"
    )
    lec = LectureSession(
        id=uuid.uuid4(),
        course_id=crs.id,
        faculty_id=faculty.id,
        title="Lecture Without Transcript",
        lecture_date=date.today(),
        duration_minutes=30,
        status="ACTIVE"
    )
    curr = Curriculum(
        id=uuid.uuid4(),
        course_id=crs.id,
        academic_term_id=term.id,
        faculty_id=faculty.id,
        title="Test Syllabus",
        document_type="SYLLABUS",
        file_name="mock.pdf",
        file_path="mock.pdf",
        file_size=512,
        mime_type="application/pdf",
        syllabus_version="v1.0"
    )
    db_session.add_all([inst, dept, user, faculty, term, crs, lec, curr])
    db_session.commit()

    exec_service = AnalysisExecutionService(db_session)
    job, _ = exec_service.start(lecture_id=lec.id, curriculum_id=curr.id, regenerate=True)
    
    run_analysis_job(job.id)
    
    db_session.refresh(job)
    assert job.status == "FAILED"
    assert "No transcript chunks are available" in job.error_message


def test_rag_retrieval_empty_query(db_session):
    """Empty query string should return 0 results cleanly without errors."""
    rag_service = RAGRetrievalService(db_session)
    res = rag_service.retrieve_evidence(query="   ", top_k=5)
    assert res.total_results == 0
    assert len(res.evidence) == 0
