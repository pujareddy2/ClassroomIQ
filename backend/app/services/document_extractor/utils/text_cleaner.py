from __future__ import annotations

import re
import unicodedata


class TextCleaner:
    """Normalize extracted text without removing academic structure."""

    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""

        normalized = unicodedata.normalize("NFKC", text)
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
        normalized = normalized.replace(" ", " ")
        normalized = re.sub(r"[​‌‍﻿]", "", normalized)
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n{2,}", "\n", normalized)
        normalized = re.sub(r"(?m)^\s*(Page|page)\s*\d+\s*$", "", normalized)
        normalized = re.sub(r"(?m)^[-•*]\s*", "- ", normalized)
        normalized = re.sub(r"[“”]", '"', normalized)
        normalized = re.sub(r"[’]", "'", normalized)
        normalized = re.sub(r"[–—]", "-", normalized)
        normalized = re.sub(r"\n(?=\S)", "\n", normalized)
        return normalized.strip()
