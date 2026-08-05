"""
Unit tests for TranscriptStatisticsCalculator.
"""

import pytest
from app.services.transcript.transcript_statistics import TranscriptStatisticsCalculator
from app.services.transcript.chunk_builder import ChunkData
from app.services.transcript.curriculum_mapper import MappingResult
from app.services.transcript.sentence_segmenter import SentenceItem
import uuid


def _sentence(idx, start, end, text="test sentence about compilers."):
    return SentenceItem(sentence_index=idx, speaker="Faculty", start=start, end=end, text=text)


def _chunk(idx, start, end, word_count=20, sentence_count=2):
    return ChunkData(chunk_index=idx, start_time=start, end_time=end, speaker="Faculty",
                     text="test chunk text", sentence_count=sentence_count, word_count=word_count)


def _mapping(idx, confidence):
    curr_id = uuid.uuid4()
    unit_id = uuid.uuid4()
    topic_id = uuid.uuid4()
    return MappingResult(
        chunk_index=idx,
        curriculum_id=curr_id,
        unit_id=unit_id,
        unit_title="Unit 1",
        chapter_id=None,
        chapter_title=None,
        topic_id=topic_id,
        topic_title="Topic A",
        confidence_score=confidence,
        mapping_reason="test match",
    )


def test_statistics_basic_counts():
    sentences = [_sentence(i, float(i * 5), float(i * 5 + 5)) for i in range(6)]
    chunks = [_chunk(1, 0.0, 30.0, word_count=40, sentence_count=3),
              _chunk(2, 30.0, 60.0, word_count=35, sentence_count=3)]
    mappings = [_mapping(1, 0.85), _mapping(2, 0.25)]

    stats = TranscriptStatisticsCalculator.calculate(sentences, chunks, mappings, [])

    assert stats.total_sentences == 6
    assert stats.total_chunks == 2
    assert stats.mapped_chunks == 1    # only confidence >= 0.30
    assert stats.unmapped_chunks == 1
    assert stats.coverage_candidates == 1  # confidence >= 0.60
    assert stats.average_chunk_length_words == 37.5
    assert stats.warnings == []


def test_statistics_all_mapped():
    sentences = [_sentence(1, 0.0, 10.0)]
    chunks = [_chunk(1, 0.0, 20.0)]
    mappings = [_mapping(1, 0.75)]

    stats = TranscriptStatisticsCalculator.calculate(sentences, chunks, mappings, [])
    assert stats.mapped_chunks == 1
    assert stats.unmapped_chunks == 0
    assert stats.coverage_candidates == 1


def test_statistics_none_mapped():
    sentences = [_sentence(1, 0.0, 5.0)]
    chunks = [_chunk(1, 0.0, 5.0, word_count=10)]
    mappings = [_mapping(1, 0.10)]

    stats = TranscriptStatisticsCalculator.calculate(sentences, chunks, mappings, [])
    assert stats.mapped_chunks == 0
    assert stats.unmapped_chunks == 1
    assert stats.coverage_candidates == 0


def test_statistics_warnings_propagated():
    sentences = [_sentence(1, 0.0, 10.0)]
    chunks = [_chunk(1, 0.0, 10.0)]
    mappings = [_mapping(1, 0.50)]
    warnings = ["Duplicate Chunk: Chunk 2 is identical", "Unmapped Chunks: 1 chunk(s) low confidence"]

    stats = TranscriptStatisticsCalculator.calculate(sentences, chunks, mappings, warnings)
    assert len(stats.warnings) == 2


def test_statistics_empty_chunks():
    stats = TranscriptStatisticsCalculator.calculate([], [], [], [])
    assert stats.total_chunks == 0
    assert stats.average_chunk_length_words == 0.0
    assert stats.average_speaking_time_seconds == 0.0
