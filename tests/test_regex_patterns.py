import pytest
import re
import sys
import os

# Import from the current directory
from regex_patterns import get_all_patterns

def test_regex_patterns():
    patterns = get_all_patterns()

    # 15+ sample academic headings
    samples = [
        ("UNIT-I", "unit"),
        ("unit 2", "unit"),
        ("MODULE II", "module"),
        ("Module-3", "module"),
        ("CHAPTER 4", "chapter"),
        ("Chapter-V", "chapter"),
        ("SECTION 1", "section"),
        ("SECTION-II", "section"),
        ("TOPIC", "topic"),
        ("TOPIC 5", "topic"),
        ("SUBTOPIC", "subtopic"),
        ("SUBTOPIC-1", "subtopic"),
        ("CO1", "co"),
        ("LO2", "lo"),
        ("PO 3", "po"),
        ("Objectives", "objectives"),
        ("Learning Outcomes", "learning_outcomes"),
        ("References", "references"),
    ]

    all_passed = True
    for text, pattern_key in samples:
        pattern = patterns.get(pattern_key)
        assert pattern is not None, f"Pattern {pattern_key} not found"

        if re.search(pattern, text):
            print(f"PASS: '{text}' matched pattern '{pattern_key}'")
        else:
            print(f"FAIL: '{text}' did not match pattern '{pattern_key}'")
            all_passed = False

    assert all_passed, "Some tests failed"
