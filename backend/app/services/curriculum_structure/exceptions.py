"""
Exceptions for curriculum structure detection.
"""


class CurriculumStructureError(Exception):
    """Base exception for curriculum structure detection errors."""
    pass


class ConfigurationError(CurriculumStructureError):
    """Raised when configuration is invalid."""
    pass


class GeminiAPIError(CurriculumStructureError):
    """Raised when Gemini API call fails."""
    pass


class ValidationError(CurriculumStructureError):
    """Raised when validation of detected structure fails."""
    pass


class ParsingError(CurriculumStructureError):
    """Raised when parsing of text fails."""
    pass