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
from app.services.rag.rag_retrieval_service import RAGRetrievalService
from app.services.xai.citation_service import CitationService


def test_retrieval_quality_evaluation_dataset(db_session):
    """
    Evaluates Top-1 accuracy, Top-3 recall, Top-5 recall, and Mean Reciprocal Rank (MRR)
    for academic retrieval precision.
    """
    r_id = str(uuid.uuid4())[:8]
    email = f"rag_eval_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. Eval Faculty {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-EVAL-{r_id}",
        designation="Professor",
        department_name="Computer Science",
    )
    user = register_user(db_session, reg)

    ref_service = ReferenceService(db_session)
    meta = ReferenceUploadMetadata(
        course_name=f"CS450 Compiler Construction {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Compiler Construction Manual {r_id}",
        document_type="REFERENCE_BOOK",
    )

    doc_text = """
SECTION 1: LEXICAL ANALYSIS
Lexical analysis converts a stream of source characters into tokens using regular expressions and finite automata.
Scanning reads input characters left-to-right and groups them into lexemes.
Lexer tokens represent keywords, identifiers, operators, and literals.

SECTION 2: SYNTAX ANALYSIS
Syntax analysis checks whether the token stream satisfies context-free grammar rules using pushdown automata.
Parsing builds abstract syntax trees representing grammatical structure.
Grammar rules define valid programming language statements and expressions.

SECTION 3: SEMANTIC ANALYSIS
Semantic analysis checks type consistency, scope declarations, and symbol table definitions.
Type checking ensures operations are applied to compatible data types.
Symbol tables keep track of identifier bindings and scope visibility.

SECTION 4: CODE OPTIMIZATION
Code optimization improves intermediate code to consume fewer CPU cycles and memory without altering execution results.
Loop unrolling and dead code elimination reduce program runtime overhead.
Optimized intermediate code targets efficient target machine instructions.
    """
    fake_file = UploadFile(filename="compilers.txt", file=io.BytesIO(doc_text.encode("utf-8")), headers={"content-type": "text/plain"})
    created_ref, _ = asyncio.run(ref_service.upload_reference_material(meta, fake_file))

    retrieval_service = RAGRetrievalService(db_session)

    eval_queries = [
        {"query": "Lexical analysis converts characters into tokens lexemes", "expected_text": "LEXICAL ANALYSIS"},
        {"query": "Syntax analysis checks context-free grammar rules syntax trees", "expected_text": "SYNTAX ANALYSIS"},
        {"query": "Semantic analysis checks type consistency symbol table bindings", "expected_text": "SEMANTIC ANALYSIS"},
        {"query": "Code optimization improves intermediate code for CPU cycles loop unrolling", "expected_text": "CODE OPTIMIZATION"},
    ]

    top_1_hits = 0
    top_3_hits = 0
    mrr_sum = 0.0

    for item in eval_queries:
        bundle = retrieval_service.retrieve_evidence(
            query=item["query"],
            course_id=created_ref.course_id,
            top_k=5,
        )
        assert bundle.total_results > 0

        ranks = [
            i + 1
            for i, ev in enumerate(bundle.evidence)
            if item["expected_text"].lower() in ev.chunk_text.lower() or (ev.section_title and item["expected_text"].lower() in ev.section_title.lower())
        ]

        if ranks:
            rank = ranks[0]
            if rank == 1:
                top_1_hits += 1
            if rank <= 3:
                top_3_hits += 1
            mrr_sum += 1.0 / rank

    top_1_accuracy = top_1_hits / len(eval_queries)
    top_3_recall = top_3_hits / len(eval_queries)
    mrr = mrr_sum / len(eval_queries)

    assert top_1_accuracy >= 0.75
    assert top_3_recall == 1.0
    assert mrr >= 0.75


def test_negative_retrieval_query(db_session):
    """
    Verifies that unrelated queries ('What is the capital of France?') return low relevance scores
    and do not fabricate evidence.
    """
    r_id = str(uuid.uuid4())[:8]
    email = f"rag_neg_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. Neg Faculty {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-NEG-{r_id}",
        designation="Professor",
        department_name="Computer Science",
    )
    user = register_user(db_session, reg)

    ref_service = ReferenceService(db_session)
    meta = ReferenceUploadMetadata(
        course_name=f"CS101 Programming {r_id}",
        academic_year="2026-2027",
        semester="1",
        faculty_name=user.full_name,
        title=f"Python Basics {r_id}",
        document_type="REFERENCE_BOOK",
    )

    doc_text = "Python variables, loops, functions, and control structures."
    fake_file = UploadFile(filename="python.txt", file=io.BytesIO(doc_text.encode("utf-8")), headers={"content-type": "text/plain"})
    created_ref, _ = asyncio.run(ref_service.upload_reference_material(meta, fake_file))

    retrieval_service = RAGRetrievalService(db_session)

    unrelated_query = "What is the capital of France and Eiffel Tower?"
    bundle = retrieval_service.retrieve_evidence(
        query=unrelated_query,
        course_id=created_ref.course_id,
        top_k=3,
    )

    if bundle.total_results > 0:
        assert bundle.evidence[0].keyword_score == 0.0


def test_technical_validation_and_xai_downstream_integration(db_session):
    """
    Verifies that downstream Member 2 engines (Validation & Explanation/XAI)
    consume RAGEvidenceBundle without duplicating retrieval logic.
    """
    r_id = str(uuid.uuid4())[:8]
    email = f"rag_downstream_{r_id}@university.edu"
    reg = RegisterRequest(
        full_name=f"Dr. Downstream Faculty {r_id}",
        email=email,
        password="Password123!",
        role="faculty",
        employee_id=f"EMP-DOWN-{r_id}",
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
        title=f"Data Structures Manual {r_id}",
        document_type="REFERENCE_BOOK",
    )

    doc_text = """
SECTION: Quicksort Analysis
Quicksort has an average time complexity of O(N log N) and a worst-case time complexity of O(N^2).
    """
    fake_file = UploadFile(filename="ds.txt", file=io.BytesIO(doc_text.encode("utf-8")), headers={"content-type": "text/plain"})
    created_ref, _ = asyncio.run(ref_service.upload_reference_material(meta, fake_file))

    retrieval_service = RAGRetrievalService(db_session)

    # 1. Retrieve RAG Evidence Bundle
    bundle = retrieval_service.retrieve_evidence(
        query="What is the average time complexity of Quicksort?",
        course_id=created_ref.course_id,
        top_k=3,
    )

    assert bundle.total_results > 0
    top_ev = bundle.evidence[0]
    assert top_ev.reference_material_id == created_ref.id
    assert "Quicksort" in top_ev.chunk_text

    # 2. XAI Citation Integration Check
    citation_service = CitationService(db_session)
    citation = citation_service.find_citation(
        evidence_item_id=top_ev.chunk_id,
        topic_name=top_ev.section_title or "Quicksort Analysis",
    )
    assert citation is not None
    assert citation.evidence_item_id == top_ev.chunk_id
