"""
regex_patterns.py

Reusable regex patterns for detecting academic markers in documents.
"""

import re

# Academic Header Patterns
# These detect unit, module, chapter, and section markers.
# They handle Roman numerals (I, V, X) and Arabic numbers.
# Example matches: "UNIT-I", "unit 2", "Module II", "CHAPTER 3"
ACADEMIC_HEADERS = {
    "unit": r"(?i)\bUNIT[-\s]+(?:[IVXLCDM]+|\d+)\b",
    "module": r"(?i)\bMODULE[-\s]+(?:[IVXLCDM]+|\d+)\b",
    "chapter": r"(?i)\bCHAPTER[-\s]+(?:[IVXLCDM]+|\d+)\b",
    "section": r"(?i)\bSECTION[-\s]+(?:[IVXLCDM]+|\d+)\b",
}

# Topic Markers
# These detect TOPIC and SUBTOPIC markers.
# Example matches: "TOPIC", "SUBTOPIC", "TOPIC 1", "SUBTOPIC-1"
TOPIC_MARKERS = {
    "topic": r"(?i)\bTOPIC(?:[-\s]+\d+)?\b",
    "subtopic": r"(?i)\bSUBTOPIC(?:[-\s]+\d+)?\b",
}

# Educational Markers
# These detect CO (Course Outcomes), LO (Learning Outcomes), PO (Program Outcomes).
# Example matches: "CO1", "CO-2", "LO3", "PO 4"
EDUCATIONAL_MARKERS = {
    "co": r"(?i)\bCO[-\s]*\d+\b",
    "lo": r"(?i)\bLO[-\s]*\d+\b",
    "po": r"(?i)\bPO[-\s]*\d+\b",
}

# Section Markers
# These detect specific sections within academic documents.
# Example matches: "Objectives", "Learning Outcomes", "References"
DOCUMENT_SECTIONS = {
    "objectives": r"(?i)\bObjectives\b",
    "learning_outcomes": r"(?i)\bLearning\s+Outcomes\b",
    "course_outcomes": r"(?i)\bCourse\s+Outcomes\b",
    "program_outcomes": r"(?i)\bProgram\s+Outcomes\b",
    "exercises": r"(?i)\bExercises\b",
    "assignments": r"(?i)\bAssignments\b",
    "references": r"(?i)\bReferences\b",
    "appendix": r"(?i)\bAppendix\b",
}

def get_all_patterns():
    """
    Returns all academic document regex patterns in one dictionary.
    """
    all_patterns = {
        **ACADEMIC_HEADERS,
        **TOPIC_MARKERS,
        **EDUCATIONAL_MARKERS,
        **DOCUMENT_SECTIONS
    }
    return all_patterns
