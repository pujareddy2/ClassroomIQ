"""
Unit tests for TopicMatcher and ReferenceRetriever.
Tests: Multiple reference books, single syllabus fallback, topic keyword containment.
"""

from app.services.validation.topic_matcher import TopicMatcher
from app.services.validation.reference_retriever import ReferenceRetriever
from app.services.curriculum_hierarchy.hierarchy_models import CurriculumSegment
import uuid


def test_topic_matcher_exact_title():
    segment = CurriculumSegment(
        segment_id="SEG_1",
        curriculum_id=uuid.uuid4(),
        unit_id=uuid.uuid4(),
        unit_title="Unit 1: Introduction",
        chapter_id=uuid.uuid4(),
        chapter_title="Chapter 1: Basics",
        topic_ids=[uuid.uuid4()],
        topic_titles=["Lexical Analysis"],
        learning_outcomes=[],
        hierarchy_path=["Unit 1", "Chapter 1"],
    )
    seg, topic_id, name, score = TopicMatcher.match_chunk_to_segment("Today we cover Lexical Analysis in detail.", [segment])
    assert seg is not None
    assert name == "Lexical Analysis"
    assert score >= 0.90


def test_reference_retriever_syllabus_fallback(db_session):
    retriever = ReferenceRetriever(db_session)
    # Even if no topic_references, returns default syllabus reference
    curr_id = uuid.uuid4()
    refs = retriever.retrieve_references_for_topic(curr_id, topic_name="Compiler")
    assert len(refs) >= 1
    assert "Curriculum" in refs[0][1] or "Syllabus" in refs[0][1]
