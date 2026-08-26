import pytest
import uuid
import io
import asyncio
from app.services.rag.semantic_chunker import SemanticChunker
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.rag_retrieval_service import RAGRetrievalService
from app.schemas.auth import RegisterRequest
from app.services.auth_service import register_user
from app.services.reference_service import ReferenceService
from app.schemas.reference_material import ReferenceUploadMetadata
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from fastapi import UploadFile


def test_semantic_chunker_basic():
    chunker = SemanticChunker(target_chunk_words=20, overlap_words=5)
    sample_text = """
CHAPTER 1: INTRODUCTION TO ALGORITHMS
An algorithm is a step-by-step procedure for solving a problem or accomplishing a task.
Algorithms form the fundamental building blocks of computer science and software development.

CHAPTER 2: DATA STRUCTURES
A data structure is a data organization, management, and storage format that enables efficient access.
Common data structures include arrays, linked lists, stacks, queues, trees, and graphs.
    """
    chunks = chunker.chunk_text(sample_text, document_title="Computer Science Fundamentals")
    assert len(chunks) >= 2
    assert chunks[0].section_title is not None
    assert chunks[0].word_count > 0
    assert chunks[0].token_count > 0


def test_embedding_service_cosine_similarity():
    service = EmbeddingService()
    text1 = "Algorithms and data structures in Python and Java"
    text2 = "Algorithms, binary trees, and Python programming"
    text3 = "Unrelated text about baking cakes and cooking recipes"

    v1 = service.generate_embedding(text1)
    v2 = service.generate_embedding(text2)
    v3 = service.generate_embedding(text3)

    assert len(v1) == 384
    assert len(v2) == 384
    assert len(v3) == 384

    sim_high = EmbeddingService.cosine_similarity(v1, v2)
    sim_low = EmbeddingService.cosine_similarity(v1, v3)

    assert sim_high > sim_low
    assert 0.0 <= sim_high <= 1.0


def test_rag_idempotent_atomic_indexing(db_session):
    r_id = str(uuid.uuid4())[:8]
    email = f"rag_idem_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. Idem Faculty {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-IDEM-{r_id}",
        designation="Professor",
        department_name="Computer Science",
    )
    user = register_user(db_session, reg)

    ref_service = ReferenceService(db_session)
    meta = ReferenceUploadMetadata(
        course_name=f"CS301 Systems {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Operating Systems Textbook {r_id}",
        document_type="REFERENCE_BOOK",
        description="OS concepts reference",
    )

    sample_doc = """
CHAPTER 1 - PROCESS MANAGEMENT
A process is an instance of a program in execution.
Process control blocks store process state, program counter, and registers.
    """
    fake_file = UploadFile(
        filename="os_textbook.txt",
        file=io.BytesIO(sample_doc.encode("utf-8")),
        headers={"content-type": "text/plain"},
    )

    created_ref, _ = asyncio.run(ref_service.upload_reference_material(meta, fake_file))
    
    rag_service = RAGRetrievalService(db_session)

    # First Indexing
    res1 = rag_service.index_reference_material(created_ref.id)
    count1 = len(rag_service.get_document_chunks(created_ref.id))

    # Re-index same document twice more
    res2 = rag_service.index_reference_material(created_ref.id)
    res3 = rag_service.index_reference_material(created_ref.id)
    count3 = len(rag_service.get_document_chunks(created_ref.id))

    # Idempotent assertion: chunk count must NOT multiply!
    assert count1 == count3
    assert res3.chunks_skipped > 0


def test_rag_multi_course_isolation(db_session):
    r_id = str(uuid.uuid4())[:8]
    email = f"rag_iso_{r_id}@university.edu"
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

    # Course A: Compiler Design
    meta_a = ReferenceUploadMetadata(
        course_name=f"CS401 Compilers {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Compilers Book {r_id}",
        document_type="REFERENCE_BOOK",
    )
    fake_file_a = UploadFile(filename="compilers.txt", file=io.BytesIO(b"Lexical analysis parses tokens."), headers={"content-type": "text/plain"})
    doc_a, _ = asyncio.run(ref_service.upload_reference_material(meta_a, fake_file_a))

    # Course B: Organic Chemistry
    meta_b = ReferenceUploadMetadata(
        course_name=f"CHEM101 Organic {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Chemistry Book {r_id}",
        document_type="REFERENCE_BOOK",
    )
    fake_file_b = UploadFile(filename="chemistry.txt", file=io.BytesIO(b"Hydrocarbons and alkane reactions."), headers={"content-type": "text/plain"})
    doc_b, _ = asyncio.run(ref_service.upload_reference_material(meta_b, fake_file_b))

    rag_service = RAGRetrievalService(db_session)

    # Query Course A -> MUST NOT return Course B evidence
    bundle_a = rag_service.retrieve_evidence(
        query="alkane reactions hydrocarbons",
        course_id=doc_a.course_id,
        top_k=5,
    )
    for ev in bundle_a.evidence:
        assert ev.reference_material_id != doc_b.id


def test_rag_api_endpoints_flow(db_session):
    r_id = str(uuid.uuid4())[:8]
    email = f"rag_api_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. RAG API Faculty {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-API-{r_id}",
        designation="Professor",
        department_name="Computer Science",
    )
    user = register_user(db_session, reg)

    ref_service = ReferenceService(db_session)
    meta = ReferenceUploadMetadata(
        course_name=f"CS201 Data Structures {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Algorithms Textbook {r_id}",
        document_type="REFERENCE_BOOK",
    )

    sample_doc = """
CHAPTER 1 - SORTING ALGORITHMS
Quicksort is an efficient sorting algorithm with O(N log N) average complexity.
    """
    fake_file = UploadFile(filename="algo.txt", file=io.BytesIO(sample_doc.encode("utf-8")), headers={"content-type": "text/plain"})
    created_ref, _ = asyncio.run(ref_service.upload_reference_material(meta, fake_file))

    client = TestClient(app)
    token = create_access_token(subject=str(user.id), extra_claims={"email": user.email, "role": user.role})
    headers = {"Authorization": f"Bearer {token}"}

    # Status API
    s_res = client.get(f"/api/v1/rag/documents/{created_ref.id}/status", headers=headers)
    assert s_res.status_code == 200
    assert s_res.json()["data"]["processing_status"] == "EMBEDDED"

    # Query API
    q_res = client.post("/api/v1/rag/query", headers=headers, json={"query": "Quicksort complexity", "course_id": str(created_ref.course_id)})
    assert q_res.status_code == 200
    evidence = q_res.json()["data"]["evidence"]
    assert len(evidence) > 0
    assert "vector_score" in evidence[0]
    assert "keyword_score" in evidence[0]
    assert "final_score" in evidence[0]

    # Reindex API
    re_res = client.post(f"/api/v1/rag/reindex/{created_ref.id}", headers=headers)
    assert re_res.status_code == 200
    assert re_res.json()["data"]["processing_status"] == "EMBEDDED"


def test_rag_precision_and_quality(db_session):
    r_id = str(uuid.uuid4())[:8]
    email = f"rag_qual_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. Quality Faculty {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-QUAL-{r_id}",
        designation="Professor",
        department_name="Computer Science",
    )
    user = register_user(db_session, reg)

    ref_service = ReferenceService(db_session)
    meta = ReferenceUploadMetadata(
        course_name=f"CS302 Compiler Design {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Compiler Design {r_id}",
        document_type="REFERENCE_BOOK",
    )

    doc_text = """
SECTION: Lexical Analysis
The lexical analyzer converts a sequence of characters into tokens for compiler processing.
    """
    fake_file = UploadFile(filename="compiler_doc.txt", file=io.BytesIO(doc_text.encode("utf-8")), headers={"content-type": "text/plain"})
    created_ref, _ = asyncio.run(ref_service.upload_reference_material(meta, fake_file))

    rag_service = RAGRetrievalService(db_session)

    # Relevant Query: "What does a lexical analyzer do?"
    rel_bundle = rag_service.retrieve_evidence(
        query="What does a lexical analyzer do?",
        course_id=created_ref.course_id,
        top_k=3,
    )
    assert rel_bundle.total_results > 0
    assert "lexical analyzer" in rel_bundle.evidence[0].chunk_text.lower()
    assert rel_bundle.evidence[0].final_score > 0.3

    # Irrelevant Query: "What is photosynthesis?"
    irrel_bundle = rag_service.retrieve_evidence(
        query="What is photosynthesis plant chlorophyll?",
        course_id=created_ref.course_id,
        top_k=3,
    )
    if irrel_bundle.total_results > 0:
        assert irrel_bundle.evidence[0].keyword_score == 0.0

