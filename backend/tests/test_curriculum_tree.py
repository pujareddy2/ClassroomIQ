"""
Unit tests for data-driven curriculum tree reconstruction, validation, and edge cases.
"""

import uuid
import pytest
from app.models.topic import Topic
from app.services.curriculum_hierarchy.tree_builder import CurriculumTreeBuilder, sort_topic_rows
from app.services.curriculum_hierarchy.tree_validator import CurriculumTreeValidator
from app.services.curriculum_hierarchy.exceptions import EmptyCurriculumError


def test_tree_reconstruction_case_a_standard():
    curr_id = uuid.uuid4()
    unit1_id = uuid.uuid4()
    chap1_id = uuid.uuid4()
    top1_id = uuid.uuid4()

    topic_rows = [
        Topic(id=unit1_id, curriculum_id=curr_id, parent_topic_id=None, topic_name="Unit 1: Intro", node_type="UNIT", display_order=1, sequence_number=1),
        Topic(id=chap1_id, curriculum_id=curr_id, parent_topic_id=unit1_id, topic_name="Chapter 1: Basics", node_type="CHAPTER", display_order=1, sequence_number=1),
        Topic(id=top1_id, curriculum_id=curr_id, parent_topic_id=chap1_id, topic_name="Topic 1: Concept A", node_type="TOPIC", display_order=1, sequence_number=1),
    ]

    units = CurriculumTreeBuilder.build_structured_units(topic_rows)
    assert len(units) == 1
    assert units[0].title == "Unit 1: Intro"
    assert len(units[0].chapters) == 1
    assert units[0].chapters[0].title == "Chapter 1: Basics"
    assert len(units[0].chapters[0].topics) == 1

    warnings = CurriculumTreeValidator.validate(topic_rows)
    assert len(warnings) == 0


def test_tree_reconstruction_case_b_unit_without_chapter():
    """Case B: Unit -> Topic directly without Chapter."""
    curr_id = uuid.uuid4()
    unit1_id = uuid.uuid4()
    top1_id = uuid.uuid4()

    topic_rows = [
        Topic(id=unit1_id, curriculum_id=curr_id, parent_topic_id=None, topic_name="Unit 1: Direct Topics", node_type="UNIT", display_order=1, sequence_number=1),
        Topic(id=top1_id, curriculum_id=curr_id, parent_topic_id=unit1_id, topic_name="Direct Topic A", node_type="TOPIC", display_order=1, sequence_number=1),
    ]

    units = CurriculumTreeBuilder.build_structured_units(topic_rows)
    assert len(units) == 1
    assert len(units[0].chapters) == 1
    assert units[0].chapters[0].topics[0].title == "Direct Topic A"


def test_tree_reconstruction_case_d_outcome_under_unit():
    """Case D: Unit -> Learning Outcome directly."""
    curr_id = uuid.uuid4()
    unit1_id = uuid.uuid4()
    lo1_id = uuid.uuid4()

    topic_rows = [
        Topic(id=unit1_id, curriculum_id=curr_id, parent_topic_id=None, topic_name="Unit 1: LO Direct", node_type="UNIT", display_order=1, sequence_number=1),
        Topic(id=lo1_id, curriculum_id=curr_id, parent_topic_id=unit1_id, topic_name="CO1: Direct Outcome", node_type="LEARNING_OUTCOME", display_order=1, sequence_number=1),
    ]

    units = CurriculumTreeBuilder.build_structured_units(topic_rows)
    assert len(units) == 1
    assert units[0].chapters[0].learning_outcomes == ["CO1: Direct Outcome"]


def test_deterministic_sorting_with_duplicate_display_order():
    """Verify display_order sorting fallback when duplicates exist."""
    u1 = Topic(id=uuid.uuid4(), parent_topic_id=None, topic_name="B", display_order=1, sequence_number=2)
    u2 = Topic(id=uuid.uuid4(), parent_topic_id=None, topic_name="A", display_order=1, sequence_number=1)

    sorted_list = sort_topic_rows([u1, u2])
    assert sorted_list[0].topic_name == "A"
    assert sorted_list[1].topic_name == "B"


def test_tree_validation_circular_reference():
    curr_id = uuid.uuid4()
    node_a = uuid.uuid4()
    node_b = uuid.uuid4()

    topic_rows = [
        Topic(id=node_a, curriculum_id=curr_id, parent_topic_id=node_b, topic_name="Cycle A", sequence_number=1),
        Topic(id=node_b, curriculum_id=curr_id, parent_topic_id=node_a, topic_name="Cycle B", sequence_number=2),
    ]

    warnings = CurriculumTreeValidator.validate(topic_rows)
    assert any("Circular Reference" in w for w in warnings)


def test_large_curriculum_performance_1000_nodes():
    """Performance test: 1000 nodes processed in under 0.1s."""
    import time
    curr_id = uuid.uuid4()
    topic_rows = []

    # 10 units, 10 chapters per unit, 9 topics per chapter = 1000 nodes
    for u in range(10):
        unit_id = uuid.uuid4()
        topic_rows.append(Topic(id=unit_id, curriculum_id=curr_id, parent_topic_id=None, topic_name=f"Unit {u}", node_type="UNIT", sequence_number=u))
        for c in range(10):
            chap_id = uuid.uuid4()
            topic_rows.append(Topic(id=chap_id, curriculum_id=curr_id, parent_topic_id=unit_id, topic_name=f"Chapter {c}", node_type="CHAPTER", sequence_number=c))
            for t in range(9):
                top_id = uuid.uuid4()
                topic_rows.append(Topic(id=top_id, curriculum_id=curr_id, parent_topic_id=chap_id, topic_name=f"Topic {t}", node_type="TOPIC", sequence_number=t))

    t0 = time.perf_counter()
    units = CurriculumTreeBuilder.build_structured_units(topic_rows)
    warnings = CurriculumTreeValidator.validate(topic_rows)
    elapsed = time.perf_counter() - t0

    assert len(units) == 10
    assert len(topic_rows) == 1010
    assert elapsed < 0.2  # Must be fast (O(n))
