from __future__ import annotations

from pathlib import Path

from app.services.document_extractor.exceptions import CorruptedDocumentError

try:
    import fitz  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    fitz = None

try:
    import pdfplumber  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pdfplumber = None


class PdfExtractor:
    """Extract text from PDFs using PyMuPDF, with pdfplumber fallback."""

    def extract(self, file_path: str | Path) -> tuple[str, str]:
        path = Path(file_path)
        if fitz is not None:
            try:
                document = fitz.open(path)
                parts = [page.get_text() for page in document]
                text = "\n\n".join(part for part in parts if part)
                document.close()
                return text, "pymupdf"
            except Exception as exc:  # pragma: no cover - fallback path
                pass

        if pdfplumber is not None:
            try:
                with pdfplumber.open(path) as document:
                    parts = [page.extract_text() or "" for page in document.pages]
                text = "\n\n".join(part for part in parts if part)
                return text, "pdfplumber"
            except Exception as exc:  # pragma: no cover - final failure
                pass

        raise CorruptedDocumentError("Unable to extract text from the PDF")
