import pytest
import sys
import os
# Ensure root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.services.curriculum_structure.regex_engine import RegexDetectionEngine
import time

def test_regex_engine_detection():
    engine = RegexDetectionEngine()

    # Realistic syllabus samples
    samples = """
UNIT-I
Introduction to AI
UNIT II
Search Algorithms
Module-3
Chapters
Chapter 1
CO1: Understand AI
LO2: Explain Search
PO 3: Apply Algorithms
Objectives
Learning Outcomes
References
Appendix
"""

    start_time = time.time()
    result = engine.detect(samples)
    execution_time = time.time() - start_time

    print("\nRegex Detection Report")
    print("-" * 25)
    print(f"Total Markers Detected: {len(result.markers)}")

    # Basic validation
    assert len(result.markers) > 0, "No markers detected"

    # Check for specific types
    marker_types = [m.marker_type for m in result.markers]
    assert "UNIT" in marker_types
    assert "CO" in marker_types

    print(f"Execution Time: {execution_time:.4f} sec")
    print("Status: PASS")

if __name__ == "__main__":
    # If run directly, execute the test
    test_regex_engine_detection()
