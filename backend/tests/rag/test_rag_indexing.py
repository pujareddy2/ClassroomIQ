import pytest
import uuid
import io
import asyncio
from fastapi import UploadFile

from app.schemas.auth import RegisterRequest
from app.services.auth_service import register_user
from app.services.reference_service import ReferenceService
from app.schemas.reference_material import ReferenceUploadMetadata
from app.services.rag.rag_indexing_service import RAGIndexingService


def test_indexing_flow_and_status(db_session):
    r_id = str(uuid.uuid4())[:8]
    email = f"rag_idx_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. Indexing Faculty {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-IDX-{r_id}",
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
        title=f"CS Intro Textbook {r_id}",
        document_type="REFERENCE_BOOK",
    )

    content = """
CHAPTER 1 - COMPUTATIONAL THINKING
Computational thinking involves breaking down complex problems into smaller, manageable parts.

CHAPTER 2 - ALGORITHMS
An algorithm provides a step-by-step clear instruction set.
    """
    fake_file = UploadFile(filename="intro.txt", file=io.BytesIO(content.encode("utf-8")), headers={"content-type": "text/plain"})
    created_ref, _ = asyncio.run(ref_service.upload_reference_material(meta, fake_file))

    indexing_service = RAGIndexingService(db_session)

    # Status check
    status_info = indexing_service.get_indexing_status(created_ref.id)
    assert status_info["processing_status"] in ("EMBEDDED", "INDEXED", "TEXT_EXTRACTED")
    assert status_info["chunk_count"] > 0
