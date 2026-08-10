from __future__ import annotations

from app.services.document_extractor.docx_extractor import DocxExtractor
from app.services.document_extractor.exceptions import UnsupportedDocumentError
from app.services.document_extractor.pdf_extractor import PdfExtractor
from app.services.document_extractor.ppt_extractor import PptExtractor
from app.services.document_extractor.txt_extractor import TxtExtractor
from app.services.document_extractor.utils.file_detector import FileDetector


class ExtractorFactory:
    """Select the correct extractor based on the file extension."""

    _extractors = {
        "pdf": PdfExtractor,
        "docx": DocxExtractor,
        "pptx": PptExtractor,
        "txt": TxtExtractor,
    }

    @classmethod
    def create(cls, file_path: str) -> object:
        kind = FileDetector.detect(file_path)
        extractor_cls = cls._extractors.get(kind)
        if extractor_cls is None:
            raise UnsupportedDocumentError(f"No extractor registered for {kind}")
        return extractor_cls()
