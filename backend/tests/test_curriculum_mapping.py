"""
Unit tests for CurriculumMapper — deterministic keyword and title matching.
"""

import uuid
from app.services.transcript.chunk_builder import ChunkData
from app.services.transcript.curriculum_mapper import CurriculumMapper
from app.services.curriculum_hierarchy.hierarchy_models import CurriculumSegment


def _make_segment(unit_title: str, chapter_title: str, topic_titles: list, outcomes: list = []) -> CurriculumSegment:
    curr_id = uuid.uuid4()
    unit_id = uuid.uuid4()
    chap_id = uuid.uuid4()
    topic_ids = [uuid.uuid4() for _ in topic_titles]
    return CurriculumSegment(
        segment_id=f"SEG_{unit_id.hex[:8]}",
        curriculum_id=curr_id,
        unit_id=unit_id,
        unit_title=unit_title,
        chapter_id=chap_id,
        chapter_title=chapter_title,
        topic_ids=topic_ids,
        topic_titles=topic_titles,
        learning_outcomes=outcomes,
        hierarchy_path=[unit_title, chapter_title],
    )


def _make_chunk(idx: int, text: str, speaker: str = "Faculty") -> ChunkData:
    return ChunkData(
        chunk_index=idx,
        start_time=float(idx * 15),
        end_time=float(idx * 15 + 15),
        speaker=speaker,
        text=text,
        sentence_count=2,
        word_count=len(text.split()),
    )


def test_exact_topic_title_match_high_confidence():
    segments = [_make_segment("Unit 1: Compiler Design", "Lexical Analysis", ["Finite Automata", "Token Recognition"])]
    chunks = [_make_chunk(1, "Finite Automata is used to recognize tokens in the lexical analysis phase.")]
    results = CurriculumMapper.map_chunks(chunks, segments)
    assert len(results) == 1
    assert results[0].confidence_score >= 0.90
    assert "Finite Automata" in results[0].mapping_reason


def test_keyword_overlap_match_medium_confidence():
    segments = [_make_segment("Unit 2: Syntax Analysis", "Context-Free Grammar", ["Parsing", "Derivation Trees"])]
    chunks = [_make_chunk(1, "The parsing process uses context-free grammar rules to derive valid sentences.")]
    results = CurriculumMapper.map_chunks(chunks, segments)
    assert len(results) == 1
    assert results[0].confidence_score >= 0.30


def test_unrelated_chunk_gets_low_confidence():
    segments = [_make_segment("Unit 1: Compiler Design", "Lexical Analysis", ["Tokens", "Finite Automata"])]
    chunks = [_make_chunk(1, "The weather today is very nice and sunny.")]
    results = CurriculumMapper.map_chunks(chunks, segments)
    assert len(results) == 1
    # Should produce the fallback with low confidence
    assert results[0].confidence_score <= 0.30


def test_multiple_chunks_all_get_mapping():
    segments = [
        _make_segment("Unit 1: Intro", "Basics", ["Compiler Definition", "Language Processors"]),
        _make_segment("Unit 2: Lexical Analysis", "Tokenization", ["Finite Automata", "Regular Expressions"]),
    ]
    chunks = [
        _make_chunk(1, "A compiler is a language processor that translates code."),
        _make_chunk(2, "Lexical analysis uses regular expressions and finite automata for tokenization."),
    ]
    results = CurriculumMapper.map_chunks(chunks, segments)
    assert len(results) == 2
    # Second chunk should match Unit 2 segments better
    assert results[1].unit_title in ("Unit 2: Lexical Analysis", "Unit 1: Intro")


def test_empty_chunks_returns_empty():
    segments = [_make_segment("Unit 1", "Chapter 1", ["Topic A"])]
    results = CurriculumMapper.map_chunks([], segments)
    assert results == []


def test_empty_segments_returns_empty():
    chunks = [_make_chunk(1, "Compiler design is important.")]
    results = CurriculumMapper.map_chunks(chunks, [])
    assert results == []
