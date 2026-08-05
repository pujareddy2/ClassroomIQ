from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from app.models.curriculum import Curriculum
from app.models.reference_material import ReferenceMaterial
from app.services.document_extractor.exceptions import DocumentExtractionError, EmptyDocumentError
from app.services.document_extractor.extractor_factory import ExtractorFactory
from app.services.document_extractor.metadata_extractor import MetadataExtractor
from app.services.document_extractor.utils.text_cleaner import TextCleaner


@dataclass(slots=True)
class ExtractedDocument:
    text: str
    metadata: dict[str, Any]


class DocumentExtractionService:
    """Service that extracts raw text from uploaded academic documents and updates existing rows."""

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def extract_text_from_path(self, file_path: str | Path) -> ExtractedDocument:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if path.stat().st_size == 0:
            raise EmptyDocumentError("The uploaded file is empty")

        started = perf_counter()
        extractor = ExtractorFactory.create(str(path))
        if hasattr(extractor, "extract"):
            if path.suffix.lower() == ".pdf":
                raw_text, library_used = extractor.extract(path)  # type: ignore[assignment]
            elif path.suffix.lower() in (".docx", ".doc"):
                raw_text = extractor.extract(path)
                library_used = "python-docx"
            elif path.suffix.lower() in (".pptx", ".ppt"):
                raw_text = extractor.extract(path)
                library_used = "python-pptx"
            else:
                raw_text = extractor.extract(path)  # type: ignore[assignment]
                library_used = "default"
        else:
            raise DocumentExtractionError("Extractor does not implement extract()")

        cleaned_text = TextCleaner.clean(raw_text)
        metadata = MetadataExtractor.build_metadata(
            path,
            library_used=library_used,
            extraction_time=perf_counter() - started,
            text=cleaned_text,
            file_size=path.stat().st_size,
        )
        return ExtractedDocument(text=cleaned_text, metadata=metadata)

    def update_document_record(self, document: Curriculum | ReferenceMaterial, extracted: ExtractedDocument) -> None:
        if self.db is None:
            return

        document.processing_status = "TEXT_EXTRACTED"
        document.file_name = extracted.metadata["file_name"]
        if hasattr(document, "extracted_text"):
            setattr(document, "extracted_text", extracted.text)
        self.db.add(document)
        self.db.flush()
