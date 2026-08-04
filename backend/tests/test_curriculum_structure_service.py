"""
Tests for the curriculum structure detection service.
"""

import pytest
from app.services.curriculum_structure.config import CurriculumStructureConfig
from app.services.curriculum_structure.service import CurriculumStructureService


def test_detect_structure_with_clear_hierarchy():
    """Test detection of a clear curriculum hierarchy."""
    config = CurriculumStructureConfig(use_fallback_regex=True)
    service = CurriculumStructureService(config=config)

    text = """
    Introduction to Physics

    Module 1: Mechanics

    Lesson 1.1: Kinematics

    Topic 1.1.1: Motion in One Dimension

    Subtopic 1.1.1.1: Displacement and Velocity

    Concept 1.1.1.1.1: Average Velocity

    Definition: Average velocity is the displacement divided by the time interval.
    """

    result = service.detect_structure(text)

    # Check that we have a program
    assert "program" in result
    program = result["program"]
    assert program["title"] == "Introduction to Physics"

    # Check that we have at least one module
    assert len(program["modules"]) > 0
    module = program["modules"][0]
    assert module["title"] == "Mechanics"

    # Check that we have lessons
    assert len(module["lessons"]) > 0
    lesson = module["lessons"][0]
    assert lesson["title"] == "Kinematics"

    # Check that we have topics
    assert len(lesson["topics"]) > 0
    topic = lesson["topics"][0]
    assert topic["title"] == "Motion in One Dimension"

    # Check that we have subtopics
    assert len(topic["subtopics"]) > 0
    subtopic = topic["subtopics"][0]
    assert subtopic["title"] == "Displacement and Velocity"

    # Check that we have concepts
    assert len(subtopic["concepts"]) > 0
    concept = subtopic["concepts"][0]
    assert concept["title"] == "Average Velocity"


def test_detect_structure_no_hierarchy():
    """Test detection when there's no clear hierarchy."""
    config = CurriculumStructureConfig(use_fallback_regex=True)
    service = CurriculumStructureService(config=config)

    text = """
    This is just a paragraph of text with no clear educational structure.
    It talks about various topics but doesn't follow a module-lesson-topic pattern.
    """

    result = service.detect_structure(text)

    # Should still return a structure (with default untitled program)
    assert "program" in result
    assert result["program"]["title"] == "Untitled Program"
    # Should have modules list (might be empty or have default)
    assert "modules" in result["program"]


def test_detect_structure_empty_text():
    """Test detection with empty text."""
    config = CurriculumStructureConfig(use_fallback_regex=True)
    service = CurriculumStructureService(config=config)

    with pytest.raises(Exception):  # Should raise ValidationError
        service.detect_structure("")


def test_detect_structure_whitespace_only():
    """Test detection with whitespace-only text."""
    config = CurriculumStructureConfig(use_fallback_regex=True)
    service = CurriculumStructureService(config=config)

    with pytest.raises(Exception):  # Should raise ValidationError
        service.detect_structure("   \n\t  \n")


if __name__ == "__main__":
    pytest.main([__file__])