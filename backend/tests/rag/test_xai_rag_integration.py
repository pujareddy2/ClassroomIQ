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
from app.services.rag.rag_indexing_service import RAGIndexingService
from app.services.rag.rag_retrieval_service import RAGRetrievalService
from app.services.xai.citation_service import CitationService
from app.services.xai.explanation_builder_service import ExplanationBuilderService


def test_xai_invokes_rag_retrieval(db_session):
    """
    TEST 1: Verify CitationService invokes RAGRetrievalService.retrieve_evidence.
    """
    citation_service = CitationService(db_session)
    dummy_ev_id = uuid.uuid4()
    
    with patch("app.services.rag.rag_retrieval_service.RAGRetrievalService.retrieve_evidence") as mock_retrieve:
        mock_retrieve.return_value.evidence = []
        mock_retrieve.return_value.total_results = 0
        
        cit = citation_service.find_citation(
            evidence_item_id=dummy_ev_id,
            topic_name="Syntax Trees",
        )
        
        assert mock_retrieve.called is True
        args, kwargs = mock_retrieve.call_args
        assert kwargs.get("query") == "Syntax Trees"
        assert cit.document_name == "Reference Not Available"
        assert cit.citation_confidence == 0.0


def test_xai_citation_points_to_real_reference(db_session):
    """
    TEST 2 & 3: Verify citation extracts metadata from indexed reference_chunks.
    """
    r_id = str(uuid.uuid4())[:8]
    email = f"xai_cit_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. XAI Faculty {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-XAI-{r_id}",
        designation="Professor",
        department_name="Computer Science",
    )
    user = register_user(db_session, reg)

    ref_service = ReferenceService(db_session)
    meta = ReferenceUploadMetadata(
        course_name=f"CS301 OS {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"OS Operating Systems {r_id}",
        document_type="REFERENCE_BOOK",
    )
    doc_text = "SECTION: Deadlock Prevention\nDeadlock prevention ensures at least one of Coffman conditions cannot hold."
    fake_file = UploadFile(filename="os.txt", file=io.BytesIO(doc_text.encode("utf-8")), headers={"content-type": "text/plain"})
    created_ref, _ = asyncio.run(ref_service.upload_reference_material(meta, fake_file))

    citation_service = CitationService(db_session)
    ev_id = uuid.uuid4()
    cit = citation_service.find_citation(
        evidence_item_id=ev_id,
        topic_name="Deadlock Prevention",
        course_id=created_ref.course_id,
    )

    assert cit.reference_material_id == created_ref.id
    assert cit.document_name == created_ref.title
    assert "Coffman" in cit.excerpt or "Deadlock" in cit.excerpt
    assert cit.citation_confidence > 0.0


def test_xai_cross_course_isolation(db_session):
    """
    TEST 6 & 7: Verify Course A citation query never returns Course B reference chunk.
    """
    r_id = str(uuid.uuid4())[:8]
    email = f"xai_iso_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. Iso Faculty {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-ISO-{r_id}",
        designation="Professor",
        department_name="Computer Science",
    )
    user = register_user(db_session, reg)

    ref_service = ReferenceService(db_session)

    # Course A
    meta_a = ReferenceUploadMetadata(
        course_name=f"CS101 A {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Course A Book {r_id}",
        document_type="REFERENCE_BOOK",
    )
    file_a = UploadFile(filename="a.txt", file=io.BytesIO(b"Data structures vectors arrays."), headers={"content-type": "text/plain"})
    ref_a, _ = asyncio.run(ref_service.upload_reference_material(meta_a, file_a))

    # Course B
    meta_b = ReferenceUploadMetadata(
        course_name=f"MATH101 B {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Course B Book {r_id}",
        document_type="REFERENCE_BOOK",
    )
    file_b = UploadFile(filename="b.txt", file=io.BytesIO(b"Calculus derivatives integration."), headers={"content-type": "text/plain"})
    ref_b, _ = asyncio.run(ref_service.upload_reference_material(meta_b, file_b))

    citation_service = CitationService(db_session)
    cit = citation_service.find_citation(
        evidence_item_id=uuid.uuid4(),
        topic_name="Calculus derivatives integration",
        course_id=ref_a.course_id,
    )

    # Must NOT return ref_b when querying under ref_a.course_id
    assert cit.reference_material_id != ref_b.id


def test_xai_empty_rag_results_sentinel(db_session):
    """
    TEST 8: Verify no fake citation is created when no RAG evidence matches.
    """
    citation_service = CitationService(db_session)
    cit = citation_service.find_citation(
        evidence_item_id=uuid.uuid4(),
        topic_name="Nonexistent Quantum Astrophysics Term 9999",
        course_id=uuid.uuid4(),
    )
    assert cit.document_name == "Reference Not Available"
    assert cit.citation_confidence == 0.0
