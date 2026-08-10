from __future__ import annotations

from pathlib import Path

from app.services.document_extractor.exceptions import UnsupportedDocumentError


class FileDetector:
    """Detect supported document types from a file path or filename."""

    SUPPORTED_EXTENSIONS = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".pptx": "pptx",
        ".txt": "txt",
    }

    @classmethod
    def detect(cls, file_path: str | Path) -> str:
        suffix = Path(file_path).suffix.lower()
        if suffix not in cls.SUPPORTED_EXTENSIONS:
            raise UnsupportedDocumentError(f"Unsupported file type: {suffix or 'unknown'}")
        return cls.SUPPORTED_EXTENSIONS[suffix]
