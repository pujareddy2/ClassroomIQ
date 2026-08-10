from __future__ import annotations

import re
import unicodedata
from typing import List


class Preprocessor:
    """Preprocesses academic text."""

    def __init__(self) -> None:
        # Patterns for academic headers/footers that should be preserved
        # Note: we don't use these in header/footer removal anymore, but we keep them for potential future use
        self.academic_patterns = [
            re.compile(
                r'^\s*UNIT\s*[-:]?\s*[IVX]+.*$',
                re.IGNORECASE,
            ),
            re.compile(
                r'^\s*CHAPTER\s*\d+.*$',
                re.IGNORECASE,
            ),
            re.compile(
                r'^\s*MODULE\s*\d+.*$',
                re.IGNORECASE,
            ),
            re.compile(
                r'^\s*CO\d+\.\d+.*$',
                re.IGNORECASE,
            ),
            re.compile(
                r'^\s*PO\d+.*$',
                re.IGNORECASE,
            ),
            re.compile(
                r'^\s*LO\d+.*$',
                re.IGNORECASE,
            ),
        ]

    def is_academic_header(self, text: str) -> bool:
        """Check if the given text matches any academic header pattern."""
        stripped = text.strip()
        for pattern in self.academic_patterns:
            if pattern.match(stripped):
                return True
        return False

    def process(self, text: str) -> str:
        """
        Process the text through the preprocessing pipeline.

        Steps:
        1. Unicode normalization
        2. Whitespace cleaning
        3. Remove page numbers (lines that are just page numbers)
        4. Remove headers and footers (repeated lines at start and end)
        5. Remove duplicate consecutive lines
        6. Remove invisible characters
        7. Final cleanup

        Args:
            text: The raw text to process.

        Returns:
            The processed text.
        """
        if not text:
            return ""

        # Step 1: Unicode normalization
        normalized = unicodedata.normalize("NFKC", text)

        # Step 2: Whitespace cleaning
        # Replace multiple spaces/tabs with a single space, and normalize line endings
        cleaned = re.sub(r"[ \t]+", " ", normalized)
        # Normalize line endings to \n
        cleaned = re.sub(r"\r\n|\r", "\n", cleaned)
        # Remove leading/trailing spaces on each line
        lines = [line.strip() for line in cleaned.split("\n")]
        # Remove empty lines that are consecutive (more than one empty line in a row)
        # We'll do this later in a more general duplicate line removal step
        cleaned = "\n".join(lines)

        # Step 3: Remove page numbers (lines that are just numbers or "Page X")
        lines = cleaned.split("\n")
        new_lines = []
        for line in lines:
            stripped = line.strip()
            # Check if the line is just a number or "Page number" (case insensitive)
            if not re.fullmatch(r"\d+", stripped) and not re.fullmatch(
                r"page\s*\d+", stripped, re.IGNORECASE
            ):
                new_lines.append(line)
            # else: skip the line (remove it)
        cleaned = "\n".join(new_lines)

        # Step 4: Remove headers and footers
        # We consider a header/footer as a line that appears at the start and end of the document.
        lines = cleaned.split("\n")
        if len(lines) >= 2:
            first_line = lines[0]
            last_line = lines[-1]
            if first_line == last_line:
                # Remove the first and last occurrence
                lines = lines[1:-1]
        cleaned = "\n".join(lines)

        # Step 5: Remove duplicate consecutive lines
        lines = cleaned.split("\n")
        if not lines:
            return ""
        new_lines = [lines[0]]
        for line in lines[1:]:
            if line != new_lines[-1]:
                new_lines.append(line)
        cleaned = "\n".join(new_lines)

        # Step 6: Remove invisible characters (zero-width spaces, etc.)
        # We already did NFKC normalization, which should remove some, but let's also remove
        # specific invisible Unicode characters.
        # We'll remove zero-width space (U+200B), zero-width non-joiner (U+200C),
        # zero-width joiner (U+200D), and byte order mark (U+FEFF).
        cleaned = re.sub(r"[​‌‍﻿]", "", cleaned)

        # Step 7: Final cleanup
        # Remove any leading/trailing whitespace that might have been introduced
        cleaned = cleaned.strip()
        # Ensure we don't have multiple empty lines at the start or end
        lines = cleaned.split("\n")
        # Remove leading empty lines
        while lines and not lines[0]:
            lines.pop(0)
        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()
        return "\n".join(lines)
