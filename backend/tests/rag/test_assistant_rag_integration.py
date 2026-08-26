import pytest
import uuid
import io
import asyncio
from unittest.mock import patch
from fastapi import UploadFile

from app.schemas.auth import RegisterRequest
from app.services.auth_service import register_user
from app.services.reference_service import ReferenceService
from app.schemas.reference_material import ReferenceUploadMetadata
from app.services.assistant.assistant_service import AssistantService
from app.services.rag.rag_retrieval_service import RAGRetrievalService


def test_assistant_invokes_rag_retrieval(db_session):
    """
    TEST 1: Verify AssistantService invokes RAGRetrievalService.retrieve_evidence.
    """
    service = AssistantService(db_session)
    
    with patch("app.services.rag.rag_retrieval_service.RAGRetrievalService.retrieve_evidence") as mock_retrieve:
        mock_retrieve.return_value.evidence = []
        mock_retrieve.return_value.total_results = 0
        
        res = service.answer_question(question="What is garbage collection?")
        
        assert mock_retrieve.called is True
        args, kwargs = mock_retrieve.call_args
        assert kwargs.get("query") == "What is garbage collection?"
        assert res["grounded"] is False
        assert res["confidence_score"] == 0.0


def test_assistant_returns_grounded_answer_with_real_chunks(db_session):
    """
    TEST 2 & 4: Verify assistant returns grounded=True and real reference_chunk sources.
    """
    r_id = str(uuid.uuid4())[:8]
    email = f"asst_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. Asst Faculty {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-ASST-{r_id}",
        designation="Professor",
        department_name="Computer Science",
    )
    user = register_user(db_session, reg)

    ref_service = ReferenceService(db_session)
    meta = ReferenceUploadMetadata(
        course_name=f"CS202 Data Structures {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Data Structures Manual {r_id}",
        document_type="REFERENCE_BOOK",
    )
    doc_text = "SECTION: Red Black Trees\nRed-black trees are self-balancing binary search trees with logarithmic time height."
    fake_file = UploadFile(filename="ds.txt", file=io.BytesIO(doc_text.encode("utf-8")), headers={"content-type": "text/plain"})
    created_ref, _ = asyncio.run(ref_service.upload_reference_material(meta, fake_file))

    service = AssistantService(db_session)
    res = service.answer_question(
        question="What is a Red Black Tree height and self balancing property?",
        course_id=created_ref.course_id,
    )

    assert res["grounded"] is True
    assert res["confidence_score"] > 0.0
    assert res["evidence_count"] >= 1
    assert res["sources"][0]["reference_material_id"] == str(created_ref.id)
    assert "Red Black" in res["answer"] or "Red-black" in res["answer"]


def test_assistant_no_evidence_fallback(db_session):
    """
    TEST 3 & 7: Verify assistant returns grounded=False and 0.0 confidence when query is unrelated.
    """
    service = AssistantService(db_session)
    res = service.answer_question(
        question="What is the distance from Earth to Jupiter in miles?",
        course_id=uuid.uuid4(),
    )

    assert res["grounded"] is False
    assert res["confidence_score"] == 0.0
    assert res["evidence_count"] == 0
    assert "couldn't find sufficient supporting material" in res["answer"]


def test_assistant_course_isolation(db_session):
    """
    TEST 6: Verify Course A assistant query never retrieves Course B reference chunk.
    """
    r_id = str(uuid.uuid4())[:8]
    email = f"asst_iso_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. Iso Asst {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-ASSTISO-{r_id}",
        designation="Professor",
        department_name="Computer Science",
    )
    user = register_user(db_session, reg)

    ref_service = ReferenceService(db_session)

    # Course A
    meta_a = ReferenceUploadMetadata(
        course_name=f"CS101 Course A {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Course A Text {r_id}",
        document_type="REFERENCE_BOOK",
    )
    file_a = UploadFile(filename="a.txt", file=io.BytesIO(b"Pointers memory allocation stack heap."), headers={"content-type": "text/plain"})
    ref_a, _ = asyncio.run(ref_service.upload_reference_material(meta_a, file_a))

    # Course B
    meta_b = ReferenceUploadMetadata(
        course_name=f"PHYS101 Course B {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Course B Text {r_id}",
        document_type="REFERENCE_BOOK",
    )
    file_b = UploadFile(filename="b.txt", file=io.BytesIO(b"Quantum mechanics wave particle duality."), headers={"content-type": "text/plain"})
    ref_b, _ = asyncio.run(ref_service.upload_reference_material(meta_b, file_b))

    service = AssistantService(db_session)
    res = service.answer_question(
        question="Quantum mechanics wave particle duality",
        course_id=ref_a.course_id,
    )

    for src in res["sources"]:
        assert src["reference_material_id"] != str(ref_b.id)
