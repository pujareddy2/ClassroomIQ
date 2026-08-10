"""
Exceptions for the Transcript Intelligence Module.
"""

class TranscriptError(Exception):
    """Base exception for transcript processing errors."""
    pass


class TranscriptValidationError(TranscriptError):
    """Raised when transcript input payload fails validation."""
    pass


class EmptyTranscriptError(TranscriptValidationError):
    """Raised when the transcript input is empty."""
    pass


class LectureNotFoundError(TranscriptError):
    """Raised when the target lecture session is not found in database."""
    pass


class MappingError(TranscriptError):
    """Raised when curriculum mapping fails critically."""
    pass
