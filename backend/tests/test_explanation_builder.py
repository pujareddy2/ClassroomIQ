"""
End-to-end integration tests for ExplanationBuilderService and SummaryService.
"""

from uuid import uuid4
import pytest
from sqlalchemy.orm import Session

from app.models.coverage_summary import CoverageSummary
from app.models.coverage_result import CoverageResult
from app.models.user import User
from app.models.faculty import Faculty
from app.models.lecture_session import LectureSession
from app.models.course import Course
from app.models.academic_term import AcademicTerm
from app.models.department import Department
from app.models.institution import Institution
from app.models.curriculum import Curriculum
from app.models.topic import Topic

from app.services.xai.evidence_collector import EvidenceCollectorService
from app.services.xai.explanation_builder_service import ExplanationBuilderService
from app.services.xai.summary_service import SummaryService
from app.repositories.xai.explanation_repository import ExplanationRepository


def _setup_coverage_data(db: Session):
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

    topic = Topic(curriculum_id=curr.id, topic_name="Pointers", sequence_number=1)
    db.add(topic)
    db.flush()

    lecture = LectureSession(course_id=course.id, faculty_id=fac.id, lecture_date=date.today())
    db.add(lecture)
    db.flush()

    cov_sum = CoverageSummary(lecture_id=lecture.id, curriculum_id=curr.id, total_topics=1, skipped_topics=1, status="ACTIVE")
    db.add(cov_sum)
    db.flush()

    cov_res = CoverageResult(
        lecture_id=lecture.id,
        curriculum_id=curr.id,
        topic_id=topic.id,
        topic_name="Pointers",
        coverage_status="SKIPPED",
        coverage_percentage=0.0,
        status="ACTIVE",
    )
    db.add(cov_res)
    db.flush()

    return lecture, curr, cov_res


def test_full_explanation_pipeline(db_session: Session):
    lecture, curr, cov_res = _setup_coverage_data(db_session)

    # 1. Collect
    collector = EvidenceCollectorService(db_session)
    bundle = collector.collect(lecture.id)
    assert len(bundle.candidates) == 1
    assert bundle.candidates[0].decision_type == "COVERAGE_SKIPPED"

    # 2. Build
    builder = ExplanationBuilderService(db_session)
    records = builder.build_all(bundle, curriculum_id=curr.id)
    assert len(records) == 1
    record = records[0]

    assert record.id is not None
    assert record.decision_source == "coverage"
    assert record.decision_type == "COVERAGE_SKIPPED"
    assert record.decision_id == cov_res.id
    assert record.overall_confidence > 0.0
    assert len(record.evidence_items) == 1
    assert len(record.reasoning_steps) == 4
    assert record.confidence_breakdown is not None
    assert record.evidence_items[0].transcript_evidence is not None
    assert record.evidence_items[0].reference_citation is not None

    # 3. Idempotency test — running build_all again returns existing active record
    records_again = builder.build_all(bundle, curriculum_id=curr.id)
    assert len(records_again) == 1
    assert records_again[0].id == record.id

    # 4. Summary
    sum_svc = SummaryService(db_session)
    summary_dict = sum_svc.compute_and_save(lecture.id, records, processing_time=0.045)
    assert summary_dict["total_explanations"] == 1
    assert summary_dict["average_confidence"] == record.overall_confidence
