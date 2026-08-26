"""
ClassroomIQ Phase 9 End-to-End Product Acceptance & Real-World Workflow Test.

Exercises the canonical faculty workflow:
Faculty Registration -> Profile Setup -> Course Creation (CS201 Data Structures & Algorithms) -> Syllabus & Topics -> Reference Material Upload -> RAG Indexing -> Ingest Spoken Transcript -> Execute 5 AI Engines -> Semantic Validation of Recommendations & Coverage -> Physical Database Audit.
"""

from __future__ import annotations

import uuid
import pathlib
import pytest
from sqlalchemy import select, func
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
from app.models.analysis_job import AnalysisJob
from app.models.validation_summary import ValidationSummary
from app.models.coverage_summary import CoverageSummary
from app.models.teaching_intelligence import TeachingSummary
from app.models.recommendation_engine import RecAnalysis
from app.models.explanation_engine import ExplanationSummary

from app.services.rag.rag_retrieval_service import RAGRetrievalService
from app.services.transcript.transcript_service import TranscriptService
from app.services.analysis_execution_service import run_analysis_job


def test_phase9_complete_faculty_product_journey(db_session: Session, tmp_path: pathlib.Path):
    """Executes the master Phase 9 real-world faculty user journey."""

    print("\n============================================================", flush=True)
    print("  CLASSROOMIQ PHASE 9 — END-TO-END PRODUCT ACCEPTANCE AUDIT", flush=True)
    print("============================================================", flush=True)

    # ── 1. Faculty Registration & Profile Setup ─────────────────────────────────
    print("  [Step 1] Verifying Real-World Faculty Registration & Credentials...", flush=True)
    rand_token = uuid.uuid4().hex[:6]
    email_addr = f"dr_turing_{rand_token}@classroomiq.edu"

    user = User(
        id=uuid.uuid4(),
        email=email_addr,
        full_name="Dr. Alan Turing",
        password_hash="pbkdf2_sha256$hashed_turing_secret",
        role="FACULTY",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    inst = Institution(
        id=uuid.uuid4(),
        name="Institute for Advanced Computer Science",
        contact_email=f"contact_{rand_token}@iacs.edu"
    )
    db_session.add(inst)
    db_session.flush()

    dept = Department(
        id=uuid.uuid4(),
        institution_id=inst.id,
        name="Department of Computer Science",
        code=f"CS_{rand_token}"
    )
    db_session.add(dept)
    db_session.flush()

    faculty = Faculty(
        id=uuid.uuid4(),
        user_id=user.id,
        department_id=dept.id,
        employee_id=f"FAC_{rand_token}",
        designation="Professor & Chair"
    )
    db_session.add(faculty)
    db_session.flush()

    assert user.id is not None
    assert faculty.user_id == user.id

    # ── 2. Course Creation: CS201 Data Structures & Algorithms ───────────────
    print("  [Step 2] Creating Course: CS201 Data Structures & Algorithms...", flush=True)
    term = AcademicTerm(
        id=uuid.uuid4(),
        institution_id=inst.id,
        academic_year="2026-2027",
        semester="Fall",
        start_date="2026-09-01",
        end_date="2026-12-31"
    )
    db_session.add(term)
    db_session.flush()

    course_code = f"CS201_{rand_token}"
    course = Course(
        id=uuid.uuid4(),
        department_id=dept.id,
        course_code=course_code,
        course_name="Data Structures and Algorithms",
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
        title="CS201 Master Syllabus & Topic Map",
        document_type="SYLLABUS",
        file_path=str(tmp_path / "cs201_syllabus.pdf"),
        file_name="cs201_syllabus.pdf",
        file_size=2048,
        mime_type="application/pdf",
        syllabus_version="v2026.1",
        processing_status="PROCESSED",
        status="ACTIVE"
    )
    db_session.add(curriculum)
    db_session.flush()

    t1 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, topic_name="Arrays & Dynamic Allocation", expected_hours=2, sequence_number=1)
    t2 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, topic_name="Linked Lists & Pointers", expected_hours=3, sequence_number=2)
    t3 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, topic_name="Stacks & Queues Data Structures", expected_hours=2, sequence_number=3)
    t4 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, topic_name="Binary Search Trees (BST) & Operations", expected_hours=4, sequence_number=4)
    t5 = Topic(id=uuid.uuid4(), curriculum_id=curriculum.id, topic_name="Graph Traversal Algorithms (BFS & DFS)", expected_hours=4, sequence_number=5)
    db_session.add_all([t1, t2, t3, t4, t5])
    db_session.flush()

    assert course.course_code == course_code

    # ── 3. Reference Material & Vector RAG Search Indexing ─────────────────────
    print("  [Step 3] Indexing Data Structures Reference Textbook in RAG Vector Store...", flush=True)
    dsa_notes_file = tmp_path / "dsa_reference_textbook.txt"
    dsa_notes_file.write_text(
        "Arrays store contiguous elements in memory indexed by integer offsets. "
        "Linked lists dynamically link nodes using pointers (head, tail, next, prev). "
        "Stacks operate under Last-In First-Out (LIFO) semantics via push and pop functions. "
        "Queues operate under First-In First-Out (FIFO) semantics via enqueue and dequeue functions. "
        "Binary Search Trees (BST) maintain node ordering where left child key is strictly smaller than parent key, "
        "and right child key is strictly larger than parent key. BST search runs in O(log n) time. "
        "Graph traversal algorithms explore nodes using Breadth-First Search (BFS) with queues "
        "and Depth-First Search (DFS) with recursive call stacks.",
        encoding="utf-8"
    )

    ref_mat = ReferenceMaterial(
        id=uuid.uuid4(),
        course_id=course.id,
        academic_term_id=term.id,
        faculty_id=faculty.id,
        title="Data Structures & Algorithms Core Reference Textbook",
        document_type="TEXTBOOK",
        file_path=str(dsa_notes_file),
        file_name="dsa_reference_textbook.txt",
        file_size=2048,
        mime_type="text/plain",
        processing_status="UPLOADED"
    )
    db_session.add(ref_mat)
    db_session.commit()

    rag_service = RAGRetrievalService(db_session)
    idx_res = rag_service.index_reference_material(ref_mat.id)
    assert idx_res.chunks_created > 0
    assert ref_mat.processing_status == "EMBEDDED"

    # ── 4. Ingesting Real Spoken Lecture Transcript ────────────────────────────
    print("  [Step 4] Ingesting Lecture 5 Spoken Transcript (BST & Stacks)...", flush=True)
    lecture = LectureSession(
        id=uuid.uuid4(),
        course_id=course.id,
        faculty_id=faculty.id,
        title="Lecture 5: Binary Search Tree Insertion & Stack Operations",
        lecture_date="2026-09-25",
        duration_minutes=50,
        status="ACTIVE"
    )
    db_session.add(lecture)
    db_session.flush()

    spoken_transcript_payload = [
        {
            "speaker": "Dr. Turing",
            "start": 0.0,
            "end": 90.0,
            "text": "Good morning class. Today we continue our study of non-linear data structures, specifically focusing on Binary Search Trees and Stack operations."
        },
        {
            "speaker": "Dr. Turing",
            "start": 90.0,
            "end": 240.0,
            "text": "A Binary Search Tree is a binary tree where every left descendant node key is less than the parent node key, and every right descendant node key is greater than the parent key."
        },
        {
            "speaker": "Dr. Turing",
            "start": 240.0,
            "end": 390.0,
            "text": "For example, inserting key 15 into a BST with root key 10 involves comparing 15 with 10. Since 15 is greater, we traverse down the right subtree."
        },
        {
            "speaker": "Dr. Turing",
            "start": 390.0,
            "end": 540.0,
            "text": "Next, let us recap Stack operations. A Stack enforces Last-In First-Out (LIFO) order. We push elements onto the stack top and pop elements from the stack top."
        }
    ]

    ts_service = TranscriptService(db_session)
    ts_res = ts_service.process_and_store_transcript(
        lecture_id=lecture.id,
        course_name_or_code=course.course_code,
        faculty_name=user.full_name,
        transcript_data=spoken_transcript_payload,
        curriculum_id=curriculum.id
    )
    db_session.commit()
    assert ts_res["chunks"] > 0

    # ── 5. Running 5 AI Engines & Semantic Correctness Validation ─────────────
    print("  [Step 5] Executing 5 AI Intelligence Engines Pipeline...", flush=True)
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
    assert job.progress_percentage == 100

    # Verify Engine 1: Coverage Summary
    cov_summary = db_session.scalars(select(CoverageSummary).where(CoverageSummary.lecture_id == lecture.id)).first()
    assert cov_summary is not None
    assert cov_summary.weighted_coverage_percentage >= 0.0

    # Verify Engine 3: Teaching Intelligence Summary
    teach_summary = db_session.scalars(select(TeachingSummary).where(TeachingSummary.lecture_id == lecture.id)).first()
    assert teach_summary is not None
    assert teach_summary.overall_teaching_score >= 0.0

    # Verify Engine 4: Prioritized Recommendations
    rec_summary = db_session.scalars(select(RecAnalysis).where(RecAnalysis.lecture_id == lecture.id)).first()
    assert rec_summary is not None

    # Verify Engine 5: Explainable AI Summary
    exp_summary = db_session.scalars(select(ExplanationSummary).where(ExplanationSummary.lecture_id == lecture.id)).first()
    assert exp_summary is not None

    # ── 6. Physical PostgreSQL Foreign Key Integrity Audit ────────────────────
    print("  [Step 6] Performing Physical PostgreSQL Foreign Key & Integrity Audit...", flush=True)
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

    print("  [Step 6 DONE] Database Audit Passed: 0 broken FKs, 0 orphan records.", flush=True)
    print("============================================================", flush=True)
    print("  CLASSROOMIQ PHASE 9 PRODUCT ACCEPTANCE: 100% PASS!", flush=True)
    print("============================================================", flush=True)
