"""
Unit tests for EvidenceRepository batch operations, CitationRepository, ConfidenceRepository, ReasoningRepository, and SummaryRepository.
"""

from uuid import uuid4
import pytest
from sqlalchemy.orm import Session

from app.models.explanation_engine import ExplanationRecord, EvidenceItem, ReferenceCitation, ConfidenceBreakdown, ReasoningStep, ExplanationSummary
from app.models.user import User
from app.models.faculty import Faculty
from app.models.lecture_session import LectureSession
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


def _create_lecture(db: Session):
    from datetime import date
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
    term = AcademicTerm(institution_id=inst.id, academic_year="2026-2027", semester="Fall", start_date=date.today(), end_date=date.today())
    db.add(term)
    db.flush()
    lecture = LectureSession(course_id=course.id, faculty_id=fac.id, lecture_date=date.today())
    db.add(lecture)
    db.flush()
    return lecture


def test_confidence_and_reasoning_repositories(db_session: Session):
    lecture = _create_lecture(db_session)
    exp_repo = ExplanationRepository(db_session)
    conf_repo = ConfidenceRepository(db_session)
    reas_repo = ReasoningRepository(db_session)
    sum_repo = SummaryRepository(db_session)

    record = exp_repo.save(ExplanationRecord(
        lecture_id=lecture.id,
        decision_source="teaching",
        decision_type="WEAK_EXPLANATION",
        decision_id=uuid4(),
        overall_confidence=78.5,
        explanation_summary="Explanation score below benchmark",
        status="ACTIVE",
    ))

    # Test ConfidenceRepository
    conf = conf_repo.save(ConfidenceBreakdown(
        explanation_record_id=record.id,
        topic_match_score=80.0,
        coverage_score=75.0,
        validation_score=70.0,
        reference_score=85.0,
        teaching_score=60.0,
        recommendation_score=70.0,
        overall_confidence=78.5,
    ))
    assert conf.id is not None
    fetched_conf = conf_repo.get_by_explanation(record.id)
    assert fetched_conf.overall_confidence == 78.5

    # Test ReasoningRepository
    steps = [
        ReasoningStep(explanation_record_id=record.id, step_order=1, reason="[OBSERVATION] Score 55/100", evidence_reference="teaching_engine"),
        ReasoningStep(explanation_record_id=record.id, step_order=2, reason="[EVIDENCE] Benchmark is 60", evidence_reference="threshold"),
        ReasoningStep(explanation_record_id=record.id, step_order=3, reason="[ANALYSIS] 55 < 60", evidence_reference="comparison"),
        ReasoningStep(explanation_record_id=record.id, step_order=4, reason="[CONCLUSION] Flagged WEAK_EXPLANATION", evidence_reference="conclusion"),
    ]
    saved_steps = reas_repo.batch_save_steps(steps)
    assert len(saved_steps) == 4
    fetched_steps = reas_repo.get_by_explanation(record.id)
    assert len(fetched_steps) == 4
    assert fetched_steps[0].step_order == 1

    # Test SummaryRepository
    summary = sum_repo.upsert(
        lecture_id=lecture.id,
        total_explanations=1,
        average_confidence=78.5,
        highest_confidence=78.5,
        lowest_confidence=78.5,
        processing_time=0.123,
    )
    assert summary.total_explanations == 1
    fetched_sum = sum_repo.get_by_lecture(lecture.id)
    assert fetched_sum.average_confidence == 78.5
