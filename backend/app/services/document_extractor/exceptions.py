class DocumentExtractionError(Exception):
    """Base exception for document extraction failures."""


class UnsupportedDocumentError(DocumentExtractionError):
    """Raised when the file type is unsupported."""


class CorruptedDocumentError(DocumentExtractionError):
    """Raised when a document cannot be read."""


class EmptyDocumentError(DocumentExtractionError):
    """Raised when an uploaded file is empty."""
