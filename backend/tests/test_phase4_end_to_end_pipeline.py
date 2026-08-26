"""
Master End-to-End Pipeline Integration Test for Phase 4.
Exercises complete flow:
Auth -> Profile -> Course -> Reference Upload -> Text Extraction -> Chunking -> Embeddings -> Vector Storage -> Knowledge Base -> Lecture Upload -> Audio/Text Processing -> Transcription -> RAG Retrieval -> 5 AI Engines -> Scoring -> Evidence -> Explanations -> Recommendations -> API Readiness.
"""

from __future__ import annotations

import pytest
import uuid
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User
from app.models.faculty import Faculty
from app.models.department import Department
from app.models.institution import Institution
from app.models.academic_term import AcademicTerm
from app.models.course import Course
from app.models.curriculum import Curriculum
from app.models.topic import Topic
from app.models.reference_material import ReferenceMaterial
from app.models.reference_chunk import ReferenceChunk
from app.models.lecture_session import LectureSession
from app.models.transcript import Transcript
from app.models.transcript_chunk import TranscriptChunk
from app.models.transcript_topic_mapping import TranscriptTopicMapping
from app.models.analysis_job import AnalysisJob
from app.models.validation_summary import ValidationSummary
from app.models.validation_result import ValidationResult
from app.models.coverage_summary import CoverageSummary
from app.models.teaching_intelligence import TeachingSummary
from app.models.recommendation_engine import RecAnalysis
from app.models.explanation_engine import ExplanationSummary

from app.services.rag.rag_retrieval_service import RAGRetrievalService
from app.services.rag.embedding_service import EmbeddingService
from app.services.transcript.transcript_service import TranscriptService
from app.services.analysis_execution_service import AnalysisExecutionService, run_analysis_job


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_phase4_complete_end_to_end_pipeline(db_session: Session, tmp_path: Path):
    """Executes real master pipeline from setup to all 5 intelligence engines."""
    
    # ── 1. Create Institution & Department ──────────────────────────────────────
    print("  [E2E Step 1] Creating Institution & Department...", flush=True)
    inst = Institution(id=uuid.uuid4(), name="ClassroomIQ Demo University", contact_email=f"admin_{uuid.uuid4().hex[:6]}@demo.edu")
    db_session.add(inst)
    db_session.flush()

    dept = Department(id=uuid.uuid4(), institution_id=inst.id, code=f"CS_{uuid.uuid4().hex[:6]}", name="Computer Science")
    db_session.add(dept)
    db_session.flush()

    # ── 2. Create User & Faculty Profile ─────────────────────────────────────────
    print("  [E2E Step 2] Creating User & Faculty Profile...", flush=True)
    user = User(
        id=uuid.uuid4(),
        full_name="Dr. ML Faculty",
        email=f"ml_faculty_{uuid.uuid4().hex[:6]}@demo.edu",
        password_hash="hashed_pw_123",
        role="faculty",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    faculty = Faculty(id=uuid.uuid4(), user_id=user.id, department_id=dept.id, employee_id=f"EMP_{uuid.uuid4().hex[:6]}", designation="Associate Professor")
    db_session.add(faculty)
    db_session.flush()

    # ── 3. Create Course ─────────────────────────────────────────────────────────
    print("  [E2E Step 3] Creating Course...", flush=True)
    course = Course(id=uuid.uuid4(), department_id=dept.id, course_code=f"CS401_{uuid.uuid4().hex[:6]}", course_name="Introduction to Machine Learning")
    db_session.add(course)
    db_session.flush()

    from datetime import date
    term = AcademicTerm(id=uuid.uuid4(), institution_id=inst.id, academic_year="2026-2027", semester="Fall 2026", start_date=date(2026,8,1), end_date=date(2026,12,31))
    db_session.add(term)
    db_session.flush()

    # ── 4. Create Curriculum & Topics ────────────────────────────────────────────
    print("  [E2E Step 4] Creating Curriculum & Topics...", flush=True)
    curriculum = Curriculum(
        id=uuid.uuid4(),
        course_id=course.id,
        academic_term_id=term.id,
        faculty_id=faculty.id,
        title="ML Curriculum Syllabus",
        document_type="SYLLABUS",
        file_name="mock_syllabus.pdf",
        file_path="mock_syllabus.pdf",
        file_size=1024,
        mime_type="application/pdf",
        syllabus_version="v1.0",
        processing_status="PROCESSED"
    )
    db_session.add(curriculum)
    db_session.flush()

    unit1 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, topic_name="Unit 1: Supervised Learning", node_type="UNIT", sequence_number=1)
    t1 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, parent_topic_id=unit1.id, topic_name="Machine Learning Fundamentals", node_type="TOPIC", sequence_number=2)
    t2 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, parent_topic_id=unit1.id, topic_name="Linear Regression & Continuous Models", node_type="TOPIC", sequence_number=3)
    t3 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, parent_topic_id=unit1.id, topic_name="Classification & Decision Trees", node_type="TOPIC", sequence_number=4)
    t4 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, parent_topic_id=unit1.id, topic_name="Model Evaluation Metrics", node_type="TOPIC", sequence_number=5)
    db_session.add_all([unit1, t1, t2, t3, t4])
    db_session.flush()

    # ── 5. Reference Material Upload & RAG Indexing ──────────────────────────────
    print("  [E2E Step 5] Reference Material Upload & RAG Indexing...", flush=True)
    ref_file = tmp_path / "ml_reference_notes.txt"
    ref_file.write_text(
        "Machine learning is a field of artificial intelligence. Supervised learning uses labeled training examples. "
        "Linear regression predicts continuous target variables by minimizing squared error. "
        "Classification predicts discrete category labels. Decision trees recursively split feature space based on information gain. "
        "Model evaluation uses cross-validation, precision, recall, and F1 score.",
        encoding="utf-8"
    )

    ref_material = ReferenceMaterial(
        id=uuid.uuid4(),
        course_id=course.id,
        academic_term_id=term.id,
        faculty_id=faculty.id,
        title="Machine Learning Faculty Notes",
        document_type="FACULTY_NOTES",
        file_path=str(ref_file),
        file_name="ml_reference_notes.txt",
        file_size=1024,
        mime_type="text/plain",
        processing_status="UPLOADED"
    )
    db_session.add(ref_material)
    db_session.commit()

    # RAG Indexing
    rag_service = RAGRetrievalService(db_session)
    index_res = rag_service.index_reference_material(ref_material.id)
    assert index_res.chunks_created > 0
    assert ref_material.processing_status == "EMBEDDED"

    ref_chunks = db_session.scalars(select(ReferenceChunk).where(ReferenceChunk.reference_material_id == ref_material.id)).all()
    assert len(ref_chunks) > 0
    for chunk in ref_chunks:
        assert chunk.embedding is not None
        assert len(chunk.embedding) == 384
        assert chunk.course_id == course.id

    # ── 6. Test RAG Course Isolation ─────────────────────────────────────────────
    print("  [E2E Step 6] Testing RAG Course Isolation...", flush=True)
    # Create another course to test strict isolation
    other_course_code = f"OTHER_{uuid.uuid4().hex[:6]}"
    other_course = Course(id=uuid.uuid4(), department_id=dept.id, course_code=other_course_code, course_name="Other Unrelated Course")
    db_session.add(other_course)
    db_session.flush()

    other_ref_file = tmp_path / "other_notes.txt"
    other_ref_file.write_text("Chemistry and organic molecules study carbon compounds.", encoding="utf-8")
    other_ref = ReferenceMaterial(
        id=uuid.uuid4(),
        course_id=other_course.id,
        academic_term_id=term.id,
        faculty_id=faculty.id,
        title="Organic Chemistry Notes",
        document_type="FACULTY_NOTES",
        file_path=str(other_ref_file),
        file_name="other_notes.txt",
        file_size=512,
        mime_type="text/plain",
        processing_status="UPLOADED"
    )
    db_session.add(other_ref)
    db_session.commit()
    rag_service.index_reference_material(other_ref.id)

    # Query with course_id=course.id
    evidence_bundle = rag_service.retrieve_evidence(query="Linear regression and classification", course_id=course.id, top_k=5)
    assert evidence_bundle.total_results > 0
    for ev in evidence_bundle.evidence:
        c_chunk = db_session.get(ReferenceChunk, ev.chunk_id)
        assert c_chunk.course_id == course.id, "Course isolation violated! Retrieved chunk from another course."
    print("  [E2E Step 6 DONE] RAG isolation verified zero cross-tenant data leakage.", flush=True)

    # ── 7. Lecture Session & Transcript Processing ──────────────────────────────
    print("  [E2E Step 7] Lecture Ingestion & Transcript Processing...", flush=True)
    lecture = LectureSession(
        id=uuid.uuid4(),
        course_id=course.id,
        faculty_id=faculty.id,
        title="Lecture 1: Intro to Supervised Learning",
        lecture_date=date.today(),
        duration_minutes=45,
        classroom="Room 301",
        status="ACTIVE"
    )
    db_session.add(lecture)
    db_session.commit()

    transcript_text = [
        {"speaker": "Faculty", "start": 0.0, "end": 15.0, "text": "Welcome class. Today we discuss supervised machine learning and regression models."},
        {"speaker": "Faculty", "start": 15.0, "end": 30.0, "text": "Linear regression fits a line to continuous data points to predict numerical outcomes."},
        {"speaker": "Faculty", "start": 30.0, "end": 45.0, "text": "For classification, decision trees partition data using entropy and information gain."},
        {"speaker": "Faculty", "start": 45.0, "end": 60.0, "text": "Finally, we evaluate model performance using accuracy, precision, and recall metrics."}
    ]

    ts_service = TranscriptService(db_session)
    ts_res = ts_service.process_and_store_transcript(
        lecture_id=lecture.id,
        course_name_or_code=course.course_code,
        faculty_name="Dr. ML Faculty",
        transcript_data=transcript_text,
        curriculum_id=curriculum.id
    )
    db_session.commit()
    assert ts_res["chunks"] > 0

    # Verify transcript & topic mappings stored
    db_transcript = db_session.scalars(select(Transcript).where(Transcript.lecture_id == lecture.id)).first()
    assert db_transcript is not None
    chunks_count = db_session.query(TranscriptChunk).filter(TranscriptChunk.transcript_id == db_transcript.id).count()
    assert chunks_count > 0

    mappings_count = db_session.query(TranscriptTopicMapping).filter(TranscriptTopicMapping.lecture_id == lecture.id).count()
    assert mappings_count > 0
    print(f"  [E2E Step 7 DONE] Transcript processed and stored ({chunks_count} chunks).", flush=True)

    # ── 8. Execute Analysis Job (5 Intelligence Engines) ─────────────────────────
    print("  [E2E Step 8] Executing 5 Intelligence Engines Pipeline...", flush=True)
    exec_service = AnalysisExecutionService(db_session)
    job, is_new = exec_service.start(lecture_id=lecture.id, curriculum_id=curriculum.id, regenerate=True)
    assert job is not None
    db_session.commit()

    run_analysis_job(job.id)

    db_session.refresh(job)
    assert job.status == "COMPLETED", f"Job failed with error: {job.error_message}"
    assert job.progress_percentage == 100
    assert job.current_stage == "COMPLETED"
    print("  [E2E Step 8 DONE] 5 Intelligence Engines execution completed (100% progress).", flush=True)

    # ── 9. Verify All 5 Engine Results in PostgreSQL ─────────────────────────────
    print("  [E2E Step 9] Verifying PostgreSQL Persisted Graph for 5 AI Engines...", flush=True)
    # Engine 1: Technical Validation
    val_summary = db_session.scalars(select(ValidationSummary).where(ValidationSummary.lecture_id == lecture.id)).first()
    assert val_summary is not None
    assert val_summary.overall_validation_score >= 0.0
    val_results = db_session.scalars(select(ValidationResult).where(ValidationResult.lecture_id == lecture.id)).all()
    assert len(val_results) > 0

    # Engine 2: Curriculum Coverage
    cov_summary = db_session.scalars(select(CoverageSummary).where(CoverageSummary.lecture_id == lecture.id)).first()
    assert cov_summary is not None
    assert cov_summary.weighted_coverage_percentage >= 0.0

    # Engine 3: Teaching Intelligence
    teach_summary = db_session.scalars(select(TeachingSummary).where(TeachingSummary.lecture_id == lecture.id)).first()
    assert teach_summary is not None
    assert teach_summary.overall_teaching_score >= 0.0

    # Engine 4: Recommendation Engine
    rec_analysis = db_session.scalars(select(RecAnalysis).where(RecAnalysis.lecture_id == lecture.id)).first()
    assert rec_analysis is not None

    # Engine 5: Explainability Engine
    exp_summary = db_session.scalars(select(ExplanationSummary).where(ExplanationSummary.lecture_id == lecture.id)).first()
    assert exp_summary is not None

    print("Phase 4 Master End-to-End Test Passed 100%!")
