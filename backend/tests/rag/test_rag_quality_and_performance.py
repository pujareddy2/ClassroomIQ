import pytest
import uuid
import time
from app.services.rag.semantic_chunker import SemanticChunker
from app.services.rag.embedding_service import EmbeddingService
from app.models.reference_chunk import ReferenceChunk


def test_chunking_zero_text_loss():
    chunker = SemanticChunker(target_chunk_words=300, overlap_words=50)
    raw_text = """
    SECTION 1: INTRODUCTION TO ALGORITHMS
    An algorithm is a finite sequence of well-defined instructions to solve a problem.

    SECTION 2: TIME COMPLEXITY
    Big O notation describes upper bound execution time growth rate.
    """
    chunks = chunker.chunk_text(raw_text)
    assert len(chunks) >= 1
    full_combined = " ".join([c.chunk_text for c in chunks])
    assert "algorithm" in full_combined.lower()
    assert "complexity" in full_combined.lower()
    assert all(c.word_count > 0 for c in chunks)


def test_embedding_vector_dimensions_and_math():
    embed_service = EmbeddingService()
    vec1 = embed_service.generate_embedding("Compiler design lexical analysis scanning")
    vec2 = embed_service.generate_embedding("Compiler design lexical analysis scanning")
    vec3 = embed_service.generate_embedding("Quantum thermodynamics black hole entropy")

    assert len(vec1) == 384
    assert all(isinstance(val, float) for val in vec1)
    
    sim_self = embed_service.cosine_similarity(vec1, vec2)
    sim_diff = embed_service.cosine_similarity(vec1, vec3)

    assert abs(sim_self - 1.0) < 1e-4
    assert sim_self > sim_diff


def test_retrieval_performance_benchmark(db_session):
    embed_service = EmbeddingService()
    latencies = []
    
    for _ in range(10):
        t0 = time.perf_counter()
        _ = embed_service.generate_embedding("Performance latency test query for academic retrieval")
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)

    avg_lat = sum(latencies) / len(latencies)
    assert avg_lat < 100.0  # Latency under 100ms
