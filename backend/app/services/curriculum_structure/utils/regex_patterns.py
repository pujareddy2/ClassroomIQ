"""
Regex patterns for curriculum structure detection.
"""

import re
from typing import Dict, List, Pattern


class CurriculumRegexPatterns:
    """Collection of regex patterns for detecting curriculum structure."""

    # Patterns for different educational levels
    PATTERNS = {
        "program": [
            re.compile(r"(?i)^\s*(program|programme|degree|course)\s*:?\s*(.+)$"),
            re.compile(r"(?i)^\s*(bachelor|master|phd|doctorate|diploma|certificate)\s+of\s+(.+)$"),
        ],
        "module": [
            re.compile(r"(?i)^\s*(module|unit|block|part)\s+(\d+|[ivxlcdm]+|[a-z])\s*:?\s*(.+)$"),
            re.compile(r"(?i)^\s*(module|unit|block|part)\s*:?\s*(.+)$"),
        ],
        "lesson": [
            re.compile(r"(?i)^\s*(lesson|lecture|session|chapter)\s+(\d+|[ivxlcdm]+|[a-z])\s*:?\s*(.+)$"),
            re.compile(r"(?i)^\s*(lesson|lecture|session|chapter)\s*:?\s*(.+)$"),
        ],
        "topic": [
            re.compile(r"(?i)^\s*(topic|subject|theme|section)\s+(\d+|[ivxlcdm]+|[a-z])\s*:?\s*(.+)$"),
            re.compile(r"(?i)^\s*(topic|subject|theme|section)\s*:?\s*(.+)$"),
        ],
        "subtopic": [
            re.compile(r"(?i)^\s*(subtopic|sub-topic|sub_section|subsection)\s+(\d+|[ivxlcdm]+|[a-z])\s*:?\s*(.+)$"),
            re.compile(r"(?i)^\s*(subtopic|sub-topic|sub_section|subsection)\s*:?\s*(.+)$"),
        ],
        "concept": [
            re.compile(r"(?i)^\s*(concept|idea|principle|theorem|law|rule)\s+(\d+|[ivxlcdm]+|[a-z])\s*:?\s*(.+)$"),
            re.compile(r"(?i)^\s*(concept|idea|principle|theorem|law|rule)\s*:?\s*(.+)$"),
        ],
    }

    # Patterns for identifying content that should be ignored (headers, footers, page numbers)
    IGNORE_PATTERNS = [
        re.compile(r"(?i)^\s*(page|pg\.?)\s*\d+\s*$"),
        re.compile(r"^\s*[\d\W]+\s*$"),  # Just numbers or non-word characters
        re.compile(r"(?i)^\s*(copyright|©|\(c\))\s*\d{4}"),
        re.compile(r"(?i)^\s*(confidential|draft|internal\s+use)"),
        re.compile(r"^\s*[\-=_]{3,}\s*$"),  # Dividers like --- or ___
    ]

    # Patterns for academic structure markers (to preserve)
    ACADEMIC_MARKERS = [
        re.compile(r"(?i)^\s*(unit|chapter|lesson|module|section|part)\s*", re.MULTILINE),
        re.compile(r"(?i)^\s*(course\s+outcome|learning\s+objective|obj)\s*[:.-]", re.MULTILINE),
        re.compile(r"(?i)^\s*(\d+(\.\d+)*)\s+[A-Z]"),  # Numbered sections like 1.1 Introduction
        re.compile(r"(?i)^\s*([IVX]+(\.\d+)*)\s+[A-Z]"),  # Roman numbered sections
    ]

    @classmethod
    def get_patterns_for_level(cls, level: str) -> List[Pattern]:
        """
        Get compiled regex patterns for a specific level.

        Args:
            level: The educational level (program, module, lesson, topic, subtopic, concept).

        Returns:
            List of compiled regex patterns.
        """
        return cls.PATTERNS.get(level, [])

    @classmethod
    def should_ignore_line(cls, line: str) -> bool:
        """
        Check if a line should be ignored (header/footer/page number).

        Args:
            line: The line to check.

        Returns:
            True if the line should be ignored, False otherwise.
        """
        return any(pattern.match(line) for pattern in cls.IGNORE_PATTERNS)

    @classmethod
    def is_academic_marker(cls, line: str) -> bool:
        """
        Check if a line contains an academic structure marker.

        Args:
            line: The line to check.

        Returns:
            True if the line is an academic marker, False otherwise.
        """
        return any(pattern.search(line) for pattern in cls.ACADEMIC_MARKERS)