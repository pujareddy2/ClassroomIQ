"""
Custom exceptions for the Technical Validation Engine.
"""


class ValidationError(Exception):
    """Base exception for validation errors."""
    pass


class EmptyTranscriptError(ValidationError):
    """Raised when the input transcript chunk list is empty."""
    pass


class CurriculumNotFoundError(ValidationError):
    """Raised when the specified curriculum cannot be found."""
    pass


class LectureNotFoundError(ValidationError):
    """Raised when the specified lecture cannot be found."""
    pass
