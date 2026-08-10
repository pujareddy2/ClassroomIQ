from __future__ import annotations

from app.services.text_preprocessor.preprocessor import Preprocessor


class TextPreprocessingService:
    """Service for preprocessing academic text."""

    def __init__(self):
        self.preprocessor = Preprocessor()

    def preprocess(self, raw_text: str) -> str:
        """
        Preprocess the raw extracted text.

        Args:
            raw_text: The raw text extracted from a document.

        Returns:
            The preprocessed text.
        """
        return self.preprocessor.process(raw_text)
