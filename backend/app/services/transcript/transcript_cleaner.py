"""
Transcript cleaner service for removing noise, fillers, repeated words, and artifacts
without altering academic content.
"""

from __future__ import annotations

import re

# Common vocal fillers to clean safely
_FILLER_WORDS_RE = re.compile(
    r"\b(?:um+|uh+|aah+|you know|like|err+)\b[,.]?",
    re.IGNORECASE,
)

# Noise markers in transcripts: [laughter], (applause), [[music]]
_NOISE_MARKERS_RE = re.compile(r"\[\[?[\w\s]+\]\]?|\([\w\s]+\)")

# Speaker prefixes: "Faculty:", "Speaker 1:"
_SPEAKER_PREFIX_RE = re.compile(r"^\s*(?:Faculty|Instructor|Professor|Speaker\s*\d+)\s*:\s*", re.IGNORECASE)

# Repeated adjacent words: "the the" -> "the"
_REPEATED_WORDS_RE = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)

# Extra spaces
_MULTIPLE_SPACES_RE = re.compile(r"\s+")


class TranscriptCleaner:
    """Cleans and normalizes transcript text."""

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""

        # 1. Remove noise markers
        cleaned = _NOISE_MARKERS_RE.sub(" ", text)

        # 2. Remove speaker prefix artifacts
        cleaned = _SPEAKER_PREFIX_RE.sub(" ", cleaned)

        # 3. Remove filler words
        cleaned = _FILLER_WORDS_RE.sub(" ", cleaned)

        # 4. Remove repeated adjacent words ("the the" -> "the")
        cleaned = _REPEATED_WORDS_RE.sub(r"\1", cleaned)

        # 5. Normalize whitespace
        cleaned = _MULTIPLE_SPACES_RE.sub(" ", cleaned).strip()

        # 6. Ensure clean punctuation spaces
        cleaned = re.sub(r"\s+([,\.!\?])", r"\1", cleaned)

        return cleaned
