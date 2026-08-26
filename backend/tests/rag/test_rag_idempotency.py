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


def test_idempotent_reindexing_does_not_duplicate(db_session):
    r_id = str(uuid.uuid4())[:8]
    email = f"rag_idem_pkg_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. Idem Pkg Faculty {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-IDEMPKG-{r_id}",
        designation="Professor",
        department_name="Computer Science",
    )
    user = register_user(db_session, reg)

    ref_service = ReferenceService(db_session)
    meta = ReferenceUploadMetadata(
        course_name=f"CS501 High Perf {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Parallel Computing {r_id}",
        document_type="REFERENCE_BOOK",
    )

    doc_text = """
SECTION 1: PARALLEL COMPUTING
Parallel computing is a type of computation in which many calculations or processes are carried out simultaneously.
    """
    fake_file = UploadFile(filename="parallel.txt", file=io.BytesIO(doc_text.encode("utf-8")), headers={"content-type": "text/plain"})
    created_ref, _ = asyncio.run(ref_service.upload_reference_material(meta, fake_file))

    indexing_service = RAGIndexingService(db_session)

    # First indexing
    res1 = indexing_service.index_reference_material(created_ref.id)
    initial_chunks = indexing_service.retrieval_service.get_document_chunks(created_ref.id)
    count1 = len(initial_chunks)

    # Re-index same document twice more
    res2 = indexing_service.reindex_reference_material(created_ref.id)
    res3 = indexing_service.reindex_reference_material(created_ref.id)
    final_chunks = indexing_service.retrieval_service.get_document_chunks(created_ref.id)
    count3 = len(final_chunks)

    assert count1 == count3
    assert res3.chunks_skipped > 0
