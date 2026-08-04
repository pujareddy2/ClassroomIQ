from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any


class MetadataExtractor:
    """Collect lightweight metadata for extracted documents."""

    @staticmethod
    def build_metadata(file_path: str | Path, *, library_used: str, extraction_time: float, text: str, file_size: int | None = None) -> dict[str, Any]:
        path = Path(file_path)
        return {
            "file_name": path.name,
            "document_type": path.suffix.lower().lstrip("."),
            "file_size": file_size or path.stat().st_size if path.exists() else 0,
            "library_used": library_used,
            "extraction_time": round(extraction_time, 4),
            "character_count": len(text),
            "word_count": len(text.split()),
            "language": "unknown",
        }
