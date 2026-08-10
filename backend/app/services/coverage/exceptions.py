"""
Custom exceptions for the Curriculum Coverage Intelligence Engine.
"""


class CoverageError(Exception):
    """Base exception for coverage errors."""
    pass


class EmptyTranscriptError(CoverageError):
    """Raised when transcript chunk list is empty."""
    pass


class CurriculumNotFoundError(CoverageError):
    """Raised when specified curriculum is not found in database."""
    pass


class LectureNotFoundError(CoverageError):
    """Raised when specified lecture session is not found in database."""
    pass


class InvalidMetadataError(CoverageError):
    """Raised when lecture or curriculum metadata validation fails."""
    pass
