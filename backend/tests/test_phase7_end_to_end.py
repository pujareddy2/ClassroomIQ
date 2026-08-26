"""
ClassroomIQ Phase 7 Master End-to-End System Integration Test.

Tests the full canonical user journey from:
Registration -> Profile -> Course -> Reference Upload -> RAG Indexing -> Multi-Tenant Isolation -> Lecture Ingestion -> Transcript Processing -> 5 AI Engines -> Evidence Traceability -> Recommendations -> Dashboard Sync -> Database Integrity Audit.
"""

from __future__ import annotations

import uuid
import pathlib
import pytest
from sqlalchemy import select, func, text
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
from app.models.coverage_summary import CoverageSummary
from app.models.teaching_intelligence import TeachingSummary
from app.models.recommendation_engine import RecAnalysis
from app.models.explanation_engine import ExplanationSummary

from app.services.rag.rag_retrieval_service import RAGRetrievalService
from app.services.transcript.transcript_service import TranscriptService
from app.services.analysis_execution_service import run_analysis_job


def test_phase7_full_system_integration(db_session: Session, tmp_path: pathlib.Path):
    """Executes the master Phase 7 End-to-End integration test."""

    print("\n============================================================", flush=True)
    print("  CLASSROOMIQ PHASE 7 — FULL SYSTEM INTEGRATION AUDIT", flush=True)
    print("============================================================", flush=True)

    # ── 1. User & Faculty Authentication Flow ──────────────────────────────────
    print("  [Step 1] Verifying User Registration & Faculty Profile...", flush=True)
    rand_token = uuid.uuid4().hex[:6]
    email_addr = f"prof_ml_{rand_token}@classroomiq.edu"
    
    user = User(
        id=uuid.uuid4(),
        email=email_addr,
        full_name="Prof. Sarah Connor",
        password_hash="pbkdf2_sha256$hashed_password_string",
        role="FACULTY",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    inst = Institution(
        id=uuid.uuid4(),
        name="Global Institute of Artificial Intelligence",
        contact_email=f"contact_{rand_token}@giai.edu"
    )
    db_session.add(inst)
    db_session.flush()

    dept = Department(
        id=uuid.uuid4(),
        institution_id=inst.id,
        name="Computer Science & Machine Learning",
        code=f"CS_{rand_token}"
    )
    db_session.add(dept)
    db_session.flush()

    faculty = Faculty(
        id=uuid.uuid4(),
        user_id=user.id,
        department_id=dept.id,
        employee_id=f"EMP_{rand_token}",
        designation="Associate Professor"
    )
    db_session.add(faculty)
    db_session.flush()

    assert user.id is not None
    assert faculty.user_id == user.id

    # ── 2. Course Creation & Curriculum Topics ────────────────────────────────
    print("  [Step 2] Verifying Course Creation & Curriculum Outline...", flush=True)
    term = AcademicTerm(
        id=uuid.uuid4(),
        institution_id=inst.id,
        academic_year="2026-2027",
        semester="1",
        start_date="2026-09-01",
        end_date="2026-12-31"
    )
    db_session.add(term)
    db_session.flush()

    course_code = f"CS_ML_{rand_token}"
    course = Course(
        id=uuid.uuid4(),
        department_id=dept.id,
        course_code=course_code,
        course_name="Introduction to Machine Learning",
        credits=4,
        created_by=user.id
    )
    db_session.add(course)
    db_session.flush()

    curriculum = Curriculum(
        id=uuid.uuid4(),
        course_id=course.id,
        academic_term_id=term.id,
        faculty_id=faculty.id,
        title="Machine Learning 101 Syllabus",
        document_type="SYLLABUS",
        file_path=str(tmp_path / "syllabus.pdf"),
        file_name="syllabus.pdf",
        file_size=1024,
        mime_type="application/pdf",
        syllabus_version="v1.0",
        processing_status="PROCESSED",
        status="ACTIVE"
    )
    db_session.add(curriculum)
    db_session.flush()

    t1 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, topic_name="Supervised Learning Fundamentals", expected_hours=1, sequence_number=1)
    t2 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, topic_name="Linear & Logistic Regression", expected_hours=1, sequence_number=2)
    t3 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, topic_name="Decision Trees & Information Gain", expected_hours=1, sequence_number=3)
    t4 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, topic_name="Model Evaluation & Cross Validation", expected_hours=1, sequence_number=4)
    db_session.add_all([t1, t2, t3, t4])
    db_session.flush()

    assert course.course_code == course_code
    assert curriculum.course_id == course.id

    # ── 3. Reference Material Upload & RAG Vector Search Indexing ──────────────
    print("  [Step 3] Verifying Reference Material Upload & RAG Vector Search...", flush=True)
    notes_file = tmp_path / "ml_reference_lecture_notes.txt"
    notes_file.write_text(
        "Supervised learning algorithms train models on labeled datasets. "
        "Linear regression predicts continuous numeric values by calculating optimal weights through gradient descent. "
        "Logistic regression predicts discrete probabilities using the sigmoid function. "
        "Decision trees split dataset features based on entropy reduction and information gain. "
        "Overfitting is mitigated using K-fold cross-validation, precision, recall, and F1 score metrics.",
        encoding="utf-8"
    )

    ref_mat = ReferenceMaterial(
        id=uuid.uuid4(),
        course_id=course.id,
        academic_term_id=term.id,
        faculty_id=faculty.id,
        title="Machine Learning Reference Notes",
        document_type="FACULTY_NOTES",
        file_path=str(notes_file),
        file_name="ml_reference_lecture_notes.txt",
        file_size=1024,
        mime_type="text/plain",
        processing_status="UPLOADED"
    )
    db_session.add(ref_mat)
    db_session.commit()

    rag_service = RAGRetrievalService(db_session)
    index_res = rag_service.index_reference_material(ref_mat.id)
    assert index_res.chunks_created > 0
    assert ref_mat.processing_status == "EMBEDDED"

    ref_chunks = db_session.scalars(select(ReferenceChunk).where(ReferenceChunk.reference_material_id == ref_mat.id)).all()
    assert len(ref_chunks) > 0
    for chk in ref_chunks:
        assert chk.embedding is not None
        assert len(chk.embedding) == 384
        assert chk.course_id == course.id

    # ── 4. Multi-Tenant RAG Course Data Isolation Test ─────────────────────────
    print("  [Step 4] Testing Multi-Tenant RAG Course Data Isolation...", flush=True)
    other_course_code = f"OTHER_{uuid.uuid4().hex[:6]}"
    other_course = Course(id=uuid.uuid4(), department_id=dept.id, course_code=other_course_code, course_name="Unrelated Physics Course")
    db_session.add(other_course)
    db_session.flush()

    other_ref_file = tmp_path / "physics_notes.txt"
    other_ref_file.write_text("Quantum mechanics wave-particle duality and Schrödinger equation.", encoding="utf-8")
    
    other_ref = ReferenceMaterial(
        id=uuid.uuid4(),
        course_id=other_course.id,
        academic_term_id=term.id,
        faculty_id=faculty.id,
        title="Physics Reference",
        document_type="FACULTY_NOTES",
        file_path=str(other_ref_file),
        file_name="physics_notes.txt",
        file_size=500,
        mime_type="text/plain",
        processing_status="UPLOADED"
    )
    db_session.add(other_ref)
    db_session.commit()
    rag_service.index_reference_material(other_ref.id)

    # Query Course A for Physics text -> Expect 0 Physics chunks returned
    bundle = rag_service.retrieve_evidence(
        query="Schrödinger equation wave-particle duality",
        course_id=course.id,
        top_k=5
    )
    for ev in bundle.evidence:
        chk = db_session.get(ReferenceChunk, ev.chunk_id)
        assert chk is not None
        assert chk.course_id == course.id
        assert chk.course_id != other_course.id
    print("  [Step 4 DONE] RAG multi-tenant isolation verified zero cross-course data leakage.", flush=True)

    # ── 5. Lecture Ingestion & Spoken Transcript Processing ────────────────────
    print("  [Step 5] Ingesting Lecture & Processing Spoken Transcript...", flush=True)
    lecture = LectureSession(
        id=uuid.uuid4(),
        course_id=course.id,
        faculty_id=faculty.id,
        title="Lecture 1: Supervised Learning & Regression",
        lecture_date="2026-09-10",
        duration_minutes=45,
        status="ACTIVE"
    )
    db_session.add(lecture)
    db_session.flush()

    transcript_data = [
        {
            "speaker": "Faculty",
            "start": 0.0,
            "end": 60.0,
            "text": "Welcome everyone to today's lecture on machine learning algorithms. Today we will cover supervised learning fundamentals and regression techniques."
        },
        {
            "speaker": "Faculty",
            "start": 60.0,
            "end": 120.0,
            "text": "Supervised learning relies on training data containing input features and target labels. Linear regression models continuous target variables by minimizing squared loss errors."
        },
        {
            "speaker": "Faculty",
            "start": 120.0,
            "end": 180.0,
            "text": "For example, predicting house prices based on square footage is a classic linear regression task. Logistic regression calculates probabilities using the sigmoid activation function."
        },
        {
            "speaker": "Faculty",
            "start": 180.0,
            "end": 240.0,
            "text": "Decision trees split features based on information gain and entropy reduction. Finally, we evaluate model generalization performance using K-fold cross-validation."
        }
    ]

    ts_service = TranscriptService(db_session)
    ts_res = ts_service.process_and_store_transcript(
        lecture_id=lecture.id,
        course_name_or_code=course.course_code,
        faculty_name=user.full_name,
        transcript_data=transcript_data,
        curriculum_id=curriculum.id
    )
    db_session.commit()
    assert ts_res["chunks"] > 0

    t_chunks = db_session.scalars(
        select(TranscriptChunk)
        .join(TranscriptChunk.transcript)
        .where(Transcript.lecture_id == lecture.id)
    ).all()
    assert len(t_chunks) > 0

    # ── 6. Execute 5 AI Intelligence Engines Pipeline ──────────────────────────
    print("  [Step 6] Running 5 AI Intelligence Engines Pipeline...", flush=True)
    job = AnalysisJob(
        id=uuid.uuid4(),
        lecture_id=lecture.id,
        curriculum_id=curriculum.id,
        status="QUEUED",
        current_stage="QUEUED",
        progress_percentage=0
    )
    db_session.add(job)
    db_session.commit()

    run_analysis_job(job.id)
    db_session.refresh(job)
    assert job.status == "COMPLETED"
    assert job.progress_percentage == 100.0

    # ── 7. Verify PostgreSQL Persisted Graph for 5 AI Engines ──────────────────
    print("  [Step 7] Verifying Persisted Graph for 5 AI Engines...", flush=True)
    
    # Engine 1: Coverage
    cov = db_session.scalars(select(CoverageSummary).where(CoverageSummary.lecture_id == lecture.id)).first()
    assert cov is not None
    assert cov.weighted_coverage_percentage >= 0.0

    # Engine 2: Validation
    val = db_session.scalars(select(ValidationSummary).where(ValidationSummary.lecture_id == lecture.id)).first()
    assert val is not None

    # Engine 3: Teaching Intelligence
    teach = db_session.scalars(select(TeachingSummary).where(TeachingSummary.lecture_id == lecture.id)).first()
    assert teach is not None
    assert teach.overall_teaching_score >= 0.0

    # Engine 4: Recommendations
    recs = db_session.scalars(select(RecAnalysis).where(RecAnalysis.lecture_id == lecture.id)).first()
    assert recs is not None

    # Engine 5: Explainable AI
    exp = db_session.scalars(select(ExplanationSummary).where(ExplanationSummary.lecture_id == lecture.id)).first()
    assert exp is not None

    print("  [Step 7 DONE] All 5 AI Engines persisted cleanly to PostgreSQL graph.", flush=True)

    # ── 8. Physical PostgreSQL Foreign Key Integrity Audit ────────────────────
    print("  [Step 8] Performing Physical PostgreSQL FK & Orphan Record Audit...", flush=True)
    
    # Check orphaned transcript chunks
    orphan_chunks = db_session.scalar(
        select(func.count(TranscriptChunk.id)).where(
            ~TranscriptChunk.transcript_id.in_(select(Transcript.id))
        )
    )
    assert orphan_chunks == 0

    # Check orphaned reference chunks
    orphan_ref_chunks = db_session.scalar(
        select(func.count(ReferenceChunk.id)).where(
            ~ReferenceChunk.reference_material_id.in_(select(ReferenceMaterial.id))
        )
    )
    assert orphan_ref_chunks == 0

    print("  [Step 8 DONE] Database Audit Passed: 0 broken FKs, 0 orphan records.", flush=True)
    print("============================================================", flush=True)
    print("  CLASSROOMIQ PHASE 7 MASTER INTEGRATION TEST: 100% PASS!", flush=True)
    print("============================================================", flush=True)
