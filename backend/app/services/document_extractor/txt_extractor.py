from __future__ import annotations

from pathlib import Path

from app.services.document_extractor.exceptions import CorruptedDocumentError, EmptyDocumentError


class TxtExtractor:
    """Extract text from plain text files using a robust encoding fallback chain."""

    def extract(self, file_path: str | Path) -> str:
        path = Path(file_path)
        if path.stat().st_size == 0:
            raise EmptyDocumentError("The uploaded text file is empty")

        for encoding in ("utf-8", "utf-16", "latin-1"):
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue

        raise CorruptedDocumentError("Unable to decode the text file with supported encodings")
