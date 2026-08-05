"""
Unit tests for curriculum segment generation.
"""

import uuid
from app.services.curriculum_hierarchy.hierarchy_models import ChapterNode, TopicNode, UnitNode
from app.services.curriculum_hierarchy.segment_builder import CurriculumSegmentBuilder


def test_curriculum_segment_builder():
    curr_id = uuid.uuid4()
    unit1_id = uuid.uuid4()
    chap1_id = uuid.uuid4()
    top1_id = uuid.uuid4()

    units = [
        UnitNode(
            id=unit1_id,
            title="Unit 1: Introduction",
            sequence_number=1,
            chapters=[
                ChapterNode(
                    id=chap1_id,
                    title="Chapter 1: History",
                    sequence_number=1,
                    topics=[TopicNode(id=top1_id, title="Need of Compiler", sequence_number=1)],
                    learning_outcomes=["CO1: Understand history"],
                )
            ],
        )
    ]

    segments = CurriculumSegmentBuilder.build_segments(curr_id, units)
    assert len(segments) == 1
    seg = segments[0]
    assert seg.curriculum_id == curr_id
    assert seg.unit_id == unit1_id
    assert seg.chapter_id == chap1_id
    assert seg.topic_titles == ["Need of Compiler"]
    assert seg.learning_outcomes == ["CO1: Understand history"]
    assert seg.display_order == 1
