import pytest
import uuid
import io
import asyncio
from datetime import date
from unittest.mock import patch
from fastapi import UploadFile
from fastapi.testclient import TestClient

from app.schemas.auth import RegisterRequest
from app.services.auth_service import register_user
from app.services.reference_service import ReferenceService
from app.schemas.reference_material import ReferenceUploadMetadata
from app.services.rag.rag_indexing_service import RAGIndexingService
from app.services.rag.rag_retrieval_service import RAGRetrievalService
from app.services.validation.validation_service import ValidationService
from app.services.validation.reference_retriever import ReferenceRetriever
from app.models.curriculum import Curriculum
from app.models.academic_term import AcademicTerm
from app.main import app
from app.core.security import create_access_token


def test_validation_rag_invocation_spy(db_session):
    """
    Test Case 28: Proves that Technical Validation Engine actually invokes
    RAGRetrievalService.retrieve_evidence() during reference lookup.
    """
    retriever = ReferenceRetriever(db_session)
    curr_id = uuid.uuid4()
    course_id = uuid.uuid4()
    
    with patch("sqlalchemy.orm.Session.get") as mock_get:
        mock_curr = Curriculum(id=curr_id, course_id=course_id, title="Mock Curr")
        mock_get.return_value = mock_curr
        
        with patch("app.services.rag.rag_retrieval_service.RAGRetrievalService.retrieve_evidence") as mock_retrieve:
            mock_retrieve.return_value.evidence = []
            mock_retrieve.return_value.total_results = 0
            
            retriever.retrieve_references_for_topic(
                curriculum_id=curr_id,
                topic_name="Lexical Analysis",
            )
            
            assert mock_retrieve.called is True
            args, kwargs = mock_retrieve.call_args
            assert kwargs.get("query") == "Lexical Analysis"
            assert kwargs.get("course_id") == course_id


def test_testcase_1_correct_concept(db_session):
    r_id = str(uuid.uuid4())[:8]
    email = f"tc1_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. TC1 Faculty {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-TC1-{r_id}",
        designation="Professor",
        department_name="Computer Science",
    )
    user = register_user(db_session, reg)

    ref_service = ReferenceService(db_session)
    meta = ReferenceUploadMetadata(
        course_name=f"CS102 Algorithms {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Algorithms Book {r_id}",
        document_type="REFERENCE_BOOK",
    )
    doc_text = "SECTION: Binary Search\nBinary search repeatedly divides the sorted search interval approximately in half."
    fake_file = UploadFile(filename="algo.txt", file=io.BytesIO(doc_text.encode("utf-8")), headers={"content-type": "text/plain"})
    created_ref, _ = asyncio.run(ref_service.upload_reference_material(meta, fake_file))

    from app.models.faculty import Faculty
    fac = db_session.query(Faculty).filter(Faculty.user_id == user.id).first()
    term = db_session.query(AcademicTerm).first()
    curr = Curriculum(
        id=uuid.uuid4(),
        course_id=created_ref.course_id,
        academic_term_id=term.id if term else uuid.uuid4(),
        faculty_id=fac.id if fac else uuid.uuid4(),
        title="Algorithms Curriculum",
        syllabus_version="1.0",
        document_type="SYLLABUS",
        file_name="algo.pdf",
        file_path="/tmp/algo.pdf",
        file_size=1024,
        mime_type="application/pdf",
    )
    db_session.add(curr)
    db_session.commit()

    val_service = ValidationService(db_session)
    chunks = [{
        "chunk_id": str(uuid.uuid4()),
        "speaker": "Faculty",
        "start_time": 0.0,
        "end_time": 60.0,
        "text": "Binary search repeatedly divides the sorted search interval approximately in half.",
    }]
    res = val_service.process_and_validate_transcript(
        transcript_chunks=chunks,
        course_id=created_ref.course_id,
        curriculum_id=curr.id,
    )
    assert res["validated_chunks"] >= 1
    assert res["status"] == "SUCCESS"


def test_testcase_5_unrelated_query(db_session):
    r_id = str(uuid.uuid4())[:8]
    email = f"tc5_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. TC5 Faculty {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-TC5-{r_id}",
        designation="Professor",
        department_name="Computer Science",
    )
    user = register_user(db_session, reg)

    ref_service = ReferenceService(db_session)
    meta = ReferenceUploadMetadata(
        course_name=f"CS101 Intro {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"CS Intro {r_id}",
        document_type="REFERENCE_BOOK",
    )
    doc_text = "Data structures, algorithms, binary search trees."
    fake_file = UploadFile(filename="intro.txt", file=io.BytesIO(doc_text.encode("utf-8")), headers={"content-type": "text/plain"})
    created_ref, _ = asyncio.run(ref_service.upload_reference_material(meta, fake_file))

    rag_service = RAGRetrievalService(db_session)
    bundle = rag_service.retrieve_evidence(
        query="What is the capital of France?",
        course_id=created_ref.course_id,
        top_k=3,
    )
    if bundle.total_results > 0:
        assert bundle.evidence[0].keyword_score == 0.0


def test_testcase_7_course_isolation(db_session):
    r_id = str(uuid.uuid4())[:8]
    email = f"tc7_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. TC7 Faculty {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-TC7-{r_id}",
        designation="Professor",
        department_name="Computer Science",
    )
    user = register_user(db_session, reg)

    ref_service = ReferenceService(db_session)

    # Course A: Compilers
    meta_a = ReferenceUploadMetadata(
        course_name=f"CS401 Compilers {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Compilers {r_id}",
        document_type="REFERENCE_BOOK",
    )
    fake_file_a = UploadFile(filename="comp.txt", file=io.BytesIO(b"Lexical analysis parses tokens."), headers={"content-type": "text/plain"})
    doc_a, _ = asyncio.run(ref_service.upload_reference_material(meta_a, fake_file_a))

    # Course B: Chemistry
    meta_b = ReferenceUploadMetadata(
        course_name=f"CHEM101 Chem {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Chemistry {r_id}",
        document_type="REFERENCE_BOOK",
    )
    fake_file_b = UploadFile(filename="chem.txt", file=io.BytesIO(b"Hydrocarbons and organic reactions."), headers={"content-type": "text/plain"})
    doc_b, _ = asyncio.run(ref_service.upload_reference_material(meta_b, fake_file_b))

    retrieval_service = RAGRetrievalService(db_session)
    bundle_a = retrieval_service.retrieve_evidence(
        query="hydrocarbons organic reactions",
        course_id=doc_a.course_id,
        top_k=5,
    )
    for ev in bundle_a.evidence:
        assert ev.reference_material_id != doc_b.id
