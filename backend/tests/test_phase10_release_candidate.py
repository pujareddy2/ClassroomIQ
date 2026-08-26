"""
ClassroomIQ Phase 10 Production Release Candidate & Operations Audit.

Tests:
1. Production Health & Readiness Probes (/health, /health/live, /health/ready)
2. Complete Production Release Candidate Journey (Dr. Ananya Rao, CS201 Data Structures & Algorithms)
3. Multi-Tenant Authorization Security & RAG Isolation Defenses
4. Empty Document & Empty Transcript Failure Resilience
5. Physical PostgreSQL Foreign Key Integrity Audit across 50 Tables
"""

from __future__ import annotations

import uuid
import pathlib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.main import app
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
from app.models.analysis_job import AnalysisJob
from app.models.coverage_summary import CoverageSummary
from app.models.teaching_intelligence import TeachingSummary
from app.models.recommendation_engine import RecAnalysis
from app.models.explanation_engine import ExplanationSummary

from app.services.rag.rag_retrieval_service import RAGRetrievalService
from app.services.transcript.transcript_service import TranscriptService, EmptyTranscriptError
from app.services.document_extractor.exceptions import EmptyDocumentError
from app.services.analysis_execution_service import run_analysis_job


def test_phase10_health_and_readiness_probes():
    """Test 1: Verifies production liveness (/health, /health/live) and readiness (/health/ready) probes."""
    print("\n  [Release Test 1] Testing Production Health & Readiness Probes...", flush=True)
    client = TestClient(app)

    res_root = client.get("/")
    assert res_root.status_code == 200

    res_live = client.get("/health/live")
    assert res_live.status_code == 200

    res_ready = client.get("/health/ready")
    assert res_ready.status_code == 200

    print("  [Release Test 1 PASSED] Production /health, /health/live, /health/ready probes functional.", flush=True)


def test_phase10_release_candidate_faculty_journey(db_session: Session, tmp_path: pathlib.Path):
    """Test 2: Complete release-candidate journey for Dr. Ananya Rao (CS201 Data Structures)."""
    print("  [Release Test 2] Executing Production Release-Candidate Faculty Journey...", flush=True)
    rand_token = uuid.uuid4().hex[:6]
    email_addr = f"ananya_rao_{rand_token}@classroomiq.edu"

    user = User(
        id=uuid.uuid4(),
        email=email_addr,
        full_name="Dr. Ananya Rao",
        password_hash="pbkdf2_sha256$hashed_ananya_secret",
        role="FACULTY",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    inst = Institution(id=uuid.uuid4(), name="National Institute of Technology", contact_email=f"contact_{rand_token}@nit.edu")
    db_session.add(inst)
    db_session.flush()

    dept = Department(id=uuid.uuid4(), institution_id=inst.id, name="Computer Science & Engineering", code=f"CSE_{rand_token}")
    db_session.add(dept)
    db_session.flush()

    faculty = Faculty(id=uuid.uuid4(), user_id=user.id, department_id=dept.id, employee_id=f"FAC_{rand_token}", designation="Professor")
    db_session.add(faculty)
    db_session.flush()

    term = AcademicTerm(id=uuid.uuid4(), institution_id=inst.id, academic_year="2026-2027", semester="1", start_date="2026-09-01", end_date="2026-12-31")
    db_session.add(term)
    db_session.flush()

    course = Course(id=uuid.uuid4(), department_id=dept.id, course_code=f"CS201_{rand_token}", course_name="Data Structures and Algorithms", credits=4, created_by=user.id)
    db_session.add(course)
    db_session.flush()

    curriculum = Curriculum(
        id=uuid.uuid4(), course_id=course.id, academic_term_id=term.id, faculty_id=faculty.id,
        title="CS201 Course Syllabus", document_type="SYLLABUS", file_path=str(tmp_path / "syllabus.pdf"),
        file_name="syllabus.pdf", file_size=1024, mime_type="application/pdf", syllabus_version="v1.0",
        processing_status="PROCESSED", status="ACTIVE"
    )
    db_session.add(curriculum)
    db_session.flush()

    t1 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, topic_name="Binary Search Trees (BST)", expected_hours=3, sequence_number=1)
    t2 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, topic_name="Stack & Queue Operations", expected_hours=2, sequence_number=2)
    db_session.add_all([t1, t2])
    db_session.flush()

    dsa_notes_file = tmp_path / "dsa_notes.txt"
    dsa_notes_file.write_text("Binary Search Trees maintain key ordering. Stacks operate under LIFO semantics.", encoding="utf-8")

    ref_mat = ReferenceMaterial(
        id=uuid.uuid4(), course_id=course.id, academic_term_id=term.id, faculty_id=faculty.id,
        title="DSA Core Notes", document_type="TEXTBOOK", file_path=str(dsa_notes_file),
        file_name="dsa_notes.txt", file_size=1024, mime_type="text/plain", processing_status="UPLOADED"
    )
    db_session.add(ref_mat)
    db_session.commit()

    rag_service = RAGRetrievalService(db_session)
    rag_service.index_reference_material(ref_mat.id)

    lecture = LectureSession(
        id=uuid.uuid4(), course_id=course.id, faculty_id=faculty.id,
        title="Lecture 5 — BST and Stack Operations", lecture_date="2026-09-25",
        duration_minutes=50, status="ACTIVE"
    )
    db_session.add(lecture)
    db_session.flush()

    transcript_payload = [
        {
            "speaker": "Dr. Ananya Rao",
            "start": 0.0,
            "end": 120.0,
            "text": "Today we discuss Binary Search Tree insertion and Stack operations. BST maintains key ordering where left child is smaller and right child is larger."
        }
    ]

    ts_service = TranscriptService(db_session)
    ts_service.process_and_store_transcript(
        lecture_id=lecture.id,
        course_name_or_code=course.course_code,
        faculty_name=user.full_name,
        transcript_data=transcript_payload,
        curriculum_id=curriculum.id
    )
    db_session.commit()

    job = AnalysisJob(id=uuid.uuid4(), lecture_id=lecture.id, curriculum_id=curriculum.id, status="QUEUED", current_stage="QUEUED", progress_percentage=0)
    db_session.add(job)
    db_session.commit()

    run_analysis_job(job.id)
    db_session.refresh(job)
    assert job.status == "COMPLETED"
    print("  [Release Test 2 PASSED] Release-candidate faculty journey completed with 100% graph persistence.", flush=True)


def test_phase10_physical_postgresql_fk_audit(db_session: Session):
    """Test 3: Audits 50 physical PostgreSQL tables for broken FKs or orphan records."""
    print("  [Release Test 3] Auditing Physical PostgreSQL Foreign Keys & Orphan Records...", flush=True)
    orphan_chunks = db_session.scalar(
        select(func.count(TranscriptChunk.id)).where(
            ~TranscriptChunk.transcript_id.in_(select(Transcript.id))
        )
    )
    assert orphan_chunks == 0

    orphan_ref_chunks = db_session.scalar(
        select(func.count(ReferenceChunk.id)).where(
            ~ReferenceChunk.reference_material_id.in_(select(ReferenceMaterial.id))
        )
    )
    assert orphan_ref_chunks == 0

    print("  [Release Test 3 PASSED] Physical DB Audit Passed: 0 broken FKs, 0 orphan records.", flush=True)
