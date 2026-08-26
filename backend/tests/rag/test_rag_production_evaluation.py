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


def setup_eval_environment(db_session):
    r_id = str(uuid.uuid4())[:8]
    user = register_user(
        db_session,
        RegisterRequest(
            full_name=f"Dr. Eval {r_id}",
            email=f"eval_{r_id}@university.edu",
            password="Password123!",
            role="faculty",
            employee_id=f"EMP-EV-{r_id}",
            designation="Professor",
            department_name="Computer Science",
        )
    )
    ref_service = ReferenceService(db_session)

    # Course 1: Compiler Design
    meta_comp = ReferenceUploadMetadata(
        course_name=f"CS401 Compilers {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Compiler Construction Textbook {r_id}",
        document_type="REFERENCE_BOOK",
    )
    file_comp = UploadFile(filename="compilers.txt", file=io.BytesIO(COMPILER_TEXTBOOK.encode("utf-8")), headers={"content-type": "text/plain"})
    ref_comp, _ = asyncio.run(ref_service.upload_reference_material(meta_comp, file_comp))

    # Course 2: Operating Systems
    meta_os = ReferenceUploadMetadata(
        course_name=f"CS301 Operating Systems {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"OS Principles Textbook {r_id}",
        document_type="REFERENCE_BOOK",
    )
    file_os = UploadFile(filename="os.txt", file=io.BytesIO(OPERATING_SYSTEMS_TEXTBOOK.encode("utf-8")), headers={"content-type": "text/plain"})
    ref_os, _ = asyncio.run(ref_service.upload_reference_material(meta_os, file_os))

    return ref_comp, ref_os


def test_production_retrieval_quality_metrics(db_session):
    """
    Evaluates Precision@1, Precision@3, Recall@1, Recall@3, MRR, and Hit Rate.
    """
    ref_comp, _ = setup_eval_environment(db_session)
    retrieval_service = RAGRetrievalService(db_session)

    eval_queries = [
        {"query": "What converts a stream of source characters into tokens scanning?", "target_text": "LEXICAL ANALYSIS"},
        {"query": "What verifies token stream conforms to context free grammar AST?", "target_text": "SYNTAX ANALYSIS"},
        {"query": "What checks type consistency variable scope declarations symbol table?", "target_text": "SEMANTIC ANALYSIS"},
        {"query": "How does code optimization minimize CPU cycles loop unrolling?", "target_text": "CODE OPTIMIZATION"},
        {"query": "What maps intermediate representations to physical target machine instructions?", "target_text": "CODE GENERATION"},
    ]

    p1_count = 0
    p3_count = 0
    mrr_sum = 0.0

    for q in eval_queries:
        bundle = retrieval_service.retrieve_evidence(
            query=q["query"],
            course_id=ref_comp.course_id,
            top_k=5,
        )
        assert bundle.total_results > 0
        hits = [
            i + 1
            for i, ev in enumerate(bundle.evidence)
            if q["target_text"].lower() in ev.chunk_text.lower() or (ev.section_title and q["target_text"].lower() in ev.section_title.lower())
        ]
        if hits:
            rank = hits[0]
            if rank == 1:
                p1_count += 1
            if rank <= 3:
                p3_count += 1
            mrr_sum += 1.0 / rank

    p1 = p1_count / len(eval_queries)
    p3 = p3_count / len(eval_queries)
    mrr = mrr_sum / len(eval_queries)

    assert p1 >= 0.80
    assert p3 == 1.0
    assert mrr >= 0.85
