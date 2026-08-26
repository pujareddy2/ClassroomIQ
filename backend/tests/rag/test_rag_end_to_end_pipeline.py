import pytest
import uuid
import io
import asyncio
from fastapi import UploadFile

from app.schemas.auth import RegisterRequest
from app.services.auth_service import register_user
from app.services.reference_service import ReferenceService
from app.schemas.reference_material import ReferenceUploadMetadata
from app.services.rag.rag_retrieval_service import RAGRetrievalService
from app.services.validation.validation_service import ValidationService
from app.services.xai.citation_service import CitationService
from app.services.coverage.coverage_service import CoverageService
from app.services.teaching.teaching_service import TeachingService
from app.services.recommendation.recommendation_service import RecommendationService
from app.services.assistant.assistant_service import AssistantService
from datetime import date
from app.models.lecture_session import LectureSession
from app.models.topic import Topic
from app.models.curriculum import Curriculum
from app.models.academic_term import AcademicTerm
from app.models.faculty import Faculty
from tests.rag.evaluation_data.compiler_and_os_dataset import COMPILER_TEXTBOOK


def test_full_end_to_end_classroomiq_rag_pipeline(db_session):
    """
    PHASE J: Full End-to-End Integration Test.
    1. Create user
    2. Create course reference
    3. Index reference material into PostgreSQL reference_chunks
    4. Run Technical Validation with RAG evidence lookup
    5. Run Explainable AI Citation binding
    6. Run Coverage Analysis
    7. Run Teaching Intelligence Analysis
    8. Generate Recommendations
    9. Ask AI Assistant a grounded academic question
    10. Verify citations, provenance, and source cards
    """
    r_id = str(uuid.uuid4())[:8]

    # 1. Create User
    user = register_user(
        db_session,
        RegisterRequest(
            full_name=f"Dr. E2E Faculty {r_id}",
            email=f"e2e_{r_id}@university.edu",
            password="Password123!",
            role="faculty",
            employee_id=f"EMP-E2E-{r_id}",
            designation="Professor",
            department_name="Computer Science",
        )
    )
    fac = db_session.query(Faculty).filter(Faculty.user_id == user.id).first()
    term = db_session.query(AcademicTerm).first()

    # 2. Upload & Index Reference Material
    ref_service = ReferenceService(db_session)
    meta = ReferenceUploadMetadata(
        course_name=f"CS401 Compilers {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Compiler Construction Textbook {r_id}",
        document_type="REFERENCE_BOOK",
    )
    fake_file = UploadFile(filename="compilers.txt", file=io.BytesIO(COMPILER_TEXTBOOK.encode("utf-8")), headers={"content-type": "text/plain"})
    created_ref, _ = asyncio.run(ref_service.upload_reference_material(meta, fake_file))

    assert created_ref.processing_status in ("INDEXED", "PROCESSED", "EMBEDDED")
    assert created_ref.course_id is not None

    # 3. Create Curriculum linked to Course
    curr = Curriculum(
        id=uuid.uuid4(),
        course_id=created_ref.course_id,
        academic_term_id=term.id if term else uuid.uuid4(),
        faculty_id=fac.id if fac else uuid.uuid4(),
        title="Compilers Syllabus",
        syllabus_version="1.0",
        document_type="SYLLABUS",
        file_name="syll.pdf",
        file_path="/tmp/syll.pdf",
        file_size=1024,
        mime_type="application/pdf",
    )
    db_session.add(curr)

    top = Topic(
        id=uuid.uuid4(),
        curriculum_id=curr.id,
        topic_name="Lexical Analysis",
        node_type="TOPIC",
        sequence_number=1,
        expected_hours=2,
    )
    db_session.add(top)
    db_session.commit()

    # 4. Create LectureSession
    lec = LectureSession(
        id=uuid.uuid4(),
        course_id=created_ref.course_id,
        faculty_id=fac.id if fac else uuid.uuid4(),
        lecture_date=date.today(),
        duration_minutes=60,
        classroom="Lab 101",
    )
    db_session.add(lec)
    db_session.commit()

    transcript_chunks = [
        {
            "chunk_id": "c1",
            "speaker": "Faculty",
            "start_time": 0.0,
            "end_time": 120.0,
            "text": "Lexical analysis converts a stream of source characters into tokens scanning.",
        },
        {
            "chunk_id": "c2",
            "speaker": "Faculty",
            "start_time": 120.0,
            "end_time": 240.0,
            "text": "Syntax analysis checks context free grammar rules using pushdown automata.",
        },
    ]

    # 5. Technical Validation Engine Integration
    val_service = ValidationService(db_session)
    val_res = val_service.process_and_validate_transcript(
        transcript_chunks=transcript_chunks,
        lecture_id=lec.id,
        course_id=created_ref.course_id,
        curriculum_id=curr.id,
    )
    assert val_res["status"] == "SUCCESS"
    assert val_res["validated_chunks"] >= 1

    # 6. Explainable AI Citation Integration
    cit_service = CitationService(db_session)
    cit = cit_service.find_citation(
        evidence_item_id=uuid.uuid4(),
        topic_name="Lexical Analysis",
        course_id=created_ref.course_id,
    )
    assert cit.reference_material_id == created_ref.id
    assert "Compiler" in cit.document_name

    # 7. Coverage Intelligence Engine Integration
    cov_service = CoverageService(db_session)
    cov_res = cov_service.analyze_lecture_coverage(
        transcript_chunks=transcript_chunks,
        lecture_id=lec.id,
        curriculum_id=curr.id,
        course_id=created_ref.course_id,
        faculty_id=user.id,
    )
    assert cov_res["lecture_id"] == str(lec.id)

    # 8. Teaching Intelligence Engine Integration
    from app.schemas.teaching import TeachingAnalyzeRequest, TranscriptChunkItem
    tch_service = TeachingService(db_session)
    chunks_items = [
        TranscriptChunkItem(chunk_id="c1", speaker="Faculty", start_time=0.0, end_time=120.0, text="Lexical analysis converts a stream of source characters into tokens scanning."),
        TranscriptChunkItem(chunk_id="c2", speaker="Faculty", start_time=120.0, end_time=240.0, text="Syntax analysis checks context free grammar rules using pushdown automata.")
    ]
    tch_req = TeachingAnalyzeRequest(lecture_id=lec.id, curriculum_id=curr.id, transcript_chunks=chunks_items)
    tch_res = tch_service.analyze_lecture_teaching(tch_req)
    assert tch_res.lecture_id == str(lec.id)

    # 9. Recommendation Engine Integration
    rec_service = RecommendationService(db_session)
    rec_res = rec_service.generate_recommendations(
        lecture_id=lec.id,
        faculty_id=user.id,
    )
    assert rec_res["total_recommendations"] >= 0

    # 10. AI Assistant Grounded RAG Query
    asst_service = AssistantService(db_session)
    asst_res = asst_service.answer_question(
        question="What are the main phases of a compiler?",
        course_id=created_ref.course_id,
        lecture_id=lec.id,
    )
    assert asst_res["grounded"] is True
    assert asst_res["confidence_score"] > 0.0
    assert len(asst_res["sources"]) >= 1
    assert asst_res["sources"][0]["reference_material_id"] == str(created_ref.id)
