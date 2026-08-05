"""
Unit tests for SemanticChunkBuilder.
Tests: short, long, multi-speaker, single sentence, and empty input.
"""

import pytest
from app.services.transcript.chunk_builder import SemanticChunkBuilder, ChunkData
from app.services.transcript.sentence_segmenter import SentenceItem


def _make_sentence(idx: int, speaker: str, start: float, end: float, text: str) -> SentenceItem:
    return SentenceItem(sentence_index=idx, speaker=speaker, start=start, end=end, text=text)


def test_chunk_builder_empty_input():
    chunks = SemanticChunkBuilder.build_chunks([])
    assert chunks == []


def test_chunk_builder_single_sentence():
    sentences = [_make_sentence(1, "Faculty", 0.0, 10.0, "Compilers translate source code to machine code.")]
    chunks = SemanticChunkBuilder.build_chunks(sentences)
    assert len(chunks) == 1
    assert chunks[0].sentence_count == 1
    assert chunks[0].word_count > 0
    assert chunks[0].start_time == 0.0
    assert chunks[0].end_time == 10.0


def test_chunk_builder_speaker_change_creates_new_chunk():
    sentences = [
        _make_sentence(1, "Faculty", 0.0, 15.0, "Compilers have multiple phases."),
        _make_sentence(2, "Student", 15.0, 25.0, "What is lexical analysis?"),
        _make_sentence(3, "Faculty", 25.0, 40.0, "Lexical analysis is the first phase."),
    ]
    chunks = SemanticChunkBuilder.build_chunks(sentences)
    # Speaker changes: Faculty → Student → Faculty  =  at least 2 different chunks
    assert len(chunks) >= 2


def test_chunk_builder_word_limit_splits_chunks():
    # Create many sentences that exceed max_word_count=140 per chunk
    sentences = [
        _make_sentence(i + 1, "Faculty", float(i * 5), float(i * 5 + 5),
                       "compiler lexical syntax semantic analysis phase tokens grammar rules production " * 3)
        for i in range(10)
    ]
    chunks = SemanticChunkBuilder.build_chunks(sentences, max_word_count=140)
    assert len(chunks) > 1


def test_chunk_builder_preserves_start_end_times():
    sentences = [
        _make_sentence(1, "Faculty", 5.0, 15.0, "Intro to compilers."),
        _make_sentence(2, "Faculty", 15.0, 30.0, "Phases of compiler design."),
    ]
    chunks = SemanticChunkBuilder.build_chunks(sentences)
    assert chunks[0].start_time == 5.0
    assert chunks[-1].end_time == 30.0


def test_chunk_builder_chunk_index_sequential():
    sentences = [
        _make_sentence(i + 1, "Faculty", float(i * 10), float(i * 10 + 10), f"Sentence {i} about compilers and lexical analysis phases.")
        for i in range(8)
    ]
    chunks = SemanticChunkBuilder.build_chunks(sentences)
    for i, c in enumerate(chunks):
        assert c.chunk_index == i + 1
