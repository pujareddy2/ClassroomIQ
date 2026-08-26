import pytest
from app.services.rag.embedding_service import EmbeddingService


def test_embedding_generation_and_dimensions():
    service = EmbeddingService()
    text = "Data structures and algorithm design patterns in Python."
    emb = service.generate_embedding(text)

    assert emb is not None
    assert len(emb) == 384
    assert isinstance(emb, list)
    assert isinstance(emb[0], float)


def test_embedding_batch_and_aliases():
    service = EmbeddingService()
    texts = ["Binary search trees", "Dynamic programming algorithms", "Graph theory and shortest paths"]
    embeddings = service.generate_embeddings(texts)

    assert len(embeddings) == 3
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384

    single_alias = service.embed_text("Test single alias")
    assert len(single_alias) == 384

    batch_alias = service.embed_texts(texts)
    assert len(batch_alias) == 3


def test_cosine_similarity_high_and_low():
    service = EmbeddingService()
    text1 = "Compiler design lexical analysis tokens"
    text2 = "Compilers scanning tokens parsing syntax"
    text3 = "Baking chocolate cake pastry dessert recipe"

    v1 = service.generate_embedding(text1)
    v2 = service.generate_embedding(text2)
    v3 = service.generate_embedding(text3)

    sim_high = EmbeddingService.cosine_similarity(v1, v2)
    sim_low = EmbeddingService.cosine_similarity(v1, v3)

    assert sim_high > sim_low
    assert 0.0 <= sim_high <= 1.0


def test_empty_input_protection():
    service = EmbeddingService()
    empty_vec = service.generate_embedding("")
    assert len(empty_vec) == 384
    assert all(x == 0.0 for x in empty_vec)
