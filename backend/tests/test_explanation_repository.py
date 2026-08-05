"""
Unit & Integration tests for ExplanationRepository and EvidenceRepository.
"""

from uuid import uuid4
import pytest
from sqlalchemy.orm import Session

from app.models.explanation_engine import ExplanationRecord, EvidenceItem, TranscriptEvidence, ReferenceCitation, ConfidenceBreakdown, ReasoningStep, ExplanationSummary
from app.models.user import User
from app.models.lecture_session import LectureSession
from app.models.faculty import Faculty
from app.models.curriculum import Curriculum
from app.models.course import Course
from app.models.academic_term import AcademicTerm
from app.models.department import Department
from app.models.institution import Institution

from app.repositories.xai.explanation_repository import ExplanationRepository
from app.repositories.xai.evidence_repository import EvidenceRepository
from app.repositories.xai.citation_repository import CitationRepository
from app.repositories.xai.confidence_repository import ConfidenceRepository
from app.repositories.xai.reasoning_repository import ReasoningRepository
from app.repositories.xai.summary_repository import SummaryRepository


def _create_mock_context(db: Session):
    inst = Institution(name="Test Inst", contact_email=f"inst_{uuid4().hex[:6]}@univ.edu")
    db.add(inst)
    db.flush()

    dept = Department(institution_id=inst.id, name="CS Dept", code=f"CS_{uuid4().hex[:6]}")
    db.add(dept)
    db.flush()

    user = User(full_name="Dr. Smith", email=f"smith_{uuid4().hex[:6]}@univ.edu", password_hash="hash", role="FACULTY")
    db.add(user)
    db.flush()

    fac = Faculty(user_id=user.id, department_id=dept.id, employee_id=f"EMP_{uuid4().hex[:6]}", designation="Professor")
    db.add(fac)
    db.flush()

    course = Course(department_id=dept.id, course_code=f"CS101_{uuid4().hex[:6]}", course_name="Intro to CS")
    db.add(course)
    db.flush()

    from datetime import date
    term = AcademicTerm(institution_id=inst.id, academic_year="2026-2027", semester="Fall", start_date=date.today(), end_date=date.today())
    db.add(term)
    db.flush()

    curr = Curriculum(
        course_id=course.id,
        academic_term_id=term.id,
        faculty_id=fac.id,
        title="CS101 Syllabus",
        document_type="SYLLABUS",
        file_name="syllabus.pdf",
        file_path="/files/syllabus.pdf",
        file_size=1024,
        mime_type="application/pdf",
        syllabus_version="v1.0",
    )
    db.add(curr)
    db.flush()

    from datetime import date
    lecture = LectureSession(course_id=course.id, faculty_id=fac.id, lecture_date=date.today())
    db.add(lecture)
    db.flush()

    return lecture, fac, curr


def test_explanation_repository_crud(db_session: Session):
    lecture, fac, curr = _create_mock_context(db_session)
    repo = ExplanationRepository(db_session)

    # 1. Save
    record = ExplanationRecord(
        lecture_id=lecture.id,
        faculty_id=fac.id,
        curriculum_id=curr.id,
        decision_source="coverage",
        decision_type="COVERAGE_SKIPPED",
        decision_id=uuid4(),
        overall_confidence=85.0,
        explanation_summary="Topic Arrays was skipped.",
        status="ACTIVE",
    )
    saved = repo.save(record)
    assert saved.id is not None

    # 2. Get active
    fetched = repo.get_active(lecture.id, "coverage", "COVERAGE_SKIPPED", record.decision_id)
    assert fetched is not None
    assert fetched.id == saved.id

    # 3. Supersede
    superseded_count = repo.supersede_existing(lecture.id, "coverage", "COVERAGE_SKIPPED", record.decision_id)
    assert superseded_count == 1

    fetched_after = repo.get_active(lecture.id, "coverage", "COVERAGE_SKIPPED", record.decision_id)
    assert fetched_after is None


def test_evidence_repository(db_session: Session):
    lecture, fac, curr = _create_mock_context(db_session)
    exp_repo = ExplanationRepository(db_session)
    ev_repo = EvidenceRepository(db_session)

    record = exp_repo.save(ExplanationRecord(
        lecture_id=lecture.id,
        decision_source="validation",
        decision_type="VALIDATION_INCORRECT",
        decision_id=uuid4(),
        overall_confidence=90.0,
        explanation_summary="Incorrect formula",
        status="ACTIVE",
    ))

    evidence = ev_repo.save_evidence_item(EvidenceItem(
        explanation_record_id=record.id,
        evidence_type="validation",
        importance_score=0.9,
    ))
    assert evidence.id is not None

    snippet = ev_repo.save_transcript_evidence(TranscriptEvidence(
        evidence_item_id=evidence.id,
        lecture_id=lecture.id,
        snippet="Faculty said 2+2=5",
        start_time=10.0,
        end_time=15.0,
    ))
    assert snippet.id is not None

    items = ev_repo.get_by_explanation(record.id)
    assert len(items) == 1
    assert items[0].transcript_evidence.snippet == "Faculty said 2+2=5"
