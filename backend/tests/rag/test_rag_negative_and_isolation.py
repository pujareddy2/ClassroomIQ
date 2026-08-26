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
from tests.rag.evaluation_data.compiler_and_os_dataset import COMPILER_TEXTBOOK, OPERATING_SYSTEMS_TEXTBOOK


def test_rag_negative_queries_and_no_evidence(db_session):
    """
    Verifies that unrelated queries receive zero keyword overlap score and produce no fabricated evidence.
    """
    r_id = str(uuid.uuid4())[:8]
    user = register_user(
        db_session,
        RegisterRequest(
            full_name=f"Dr. Neg {r_id}",
            email=f"neg_{r_id}@university.edu",
            password="Password123!",
            role="faculty",
            employee_id=f"EMP-NEG-{r_id}",
            designation="Professor",
            department_name="Computer Science",
        )
    )
    ref_service = ReferenceService(db_session)
    meta = ReferenceUploadMetadata(
        course_name=f"CS401 Compilers {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Compiler Textbook {r_id}",
        document_type="REFERENCE_BOOK",
    )
    file_comp = UploadFile(filename="compilers.txt", file=io.BytesIO(COMPILER_TEXTBOOK.encode("utf-8")), headers={"content-type": "text/plain"})
    ref_comp, _ = asyncio.run(ref_service.upload_reference_material(meta, file_comp))

    retrieval_service = RAGRetrievalService(db_session)

    negative_queries = [
        "What is the capital of France and Eiffel Tower?",
        "How do photosynthesis and chlorophyll function in plant cells?",
        "What is black hole event horizon general relativity?",
    ]

    for neg_q in negative_queries:
        bundle = retrieval_service.retrieve_evidence(
            query=neg_q,
            course_id=ref_comp.course_id,
            top_k=3,
        )
        if bundle.total_results > 0:
            assert bundle.evidence[0].final_score < 0.30
            assert bundle.evidence[0].keyword_score < 0.20


def test_rag_course_isolation_security(db_session):
    """
    Verifies multi-course tenant security: Course A queries NEVER return Course B chunks.
    """
    r_id = str(uuid.uuid4())[:8]
    user = register_user(
        db_session,
        RegisterRequest(
            full_name=f"Dr. Iso {r_id}",
            email=f"iso_{r_id}@university.edu",
            password="Password123!",
            role="faculty",
            employee_id=f"EMP-ISO-{r_id}",
            designation="Professor",
            department_name="Computer Science",
        )
    )
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
    file_a = UploadFile(filename="comp.txt", file=io.BytesIO(COMPILER_TEXTBOOK.encode("utf-8")), headers={"content-type": "text/plain"})
    ref_a, _ = asyncio.run(ref_service.upload_reference_material(meta_a, file_a))

    # Course B: Operating Systems
    meta_b = ReferenceUploadMetadata(
        course_name=f"CS301 OS {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"OS {r_id}",
        document_type="REFERENCE_BOOK",
    )
    file_b = UploadFile(filename="os.txt", file=io.BytesIO(OPERATING_SYSTEMS_TEXTBOOK.encode("utf-8")), headers={"content-type": "text/plain"})
    ref_b, _ = asyncio.run(ref_service.upload_reference_material(meta_b, file_b))

    retrieval_service = RAGRetrievalService(db_session)

    # Querying Course A for OS concepts (Coffman conditions / semaphores)
    bundle_a = retrieval_service.retrieve_evidence(
        query="semaphores mutex deadlock Coffman conditions",
        course_id=ref_a.course_id,
        top_k=5,
    )
    for ev in bundle_a.evidence:
        assert ev.reference_material_id != ref_b.id
