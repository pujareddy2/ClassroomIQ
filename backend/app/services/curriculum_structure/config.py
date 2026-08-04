"""
Configuration for curriculum structure detection.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class CurriculumStructureConfig:
    """Configuration for curriculum structure detection."""

    # Gemini API settings
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-pro"
    gemini_temperature: float = 0.1
    gemini_max_output_tokens: int = 8192

    # Fallback settings
    use_fallback_regex: bool = True
    fallback_confidence_threshold: float = 0.7

    # Processing settings
    min_section_length: int = 10
    max_section_length: int = 10000
    preserve_academic_structure: bool = True

    # Output settings
    output_format: str = "json"  # or "yaml"
    validate_schema: bool = True

    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None

    @classmethod
    def from_env(cls) -> "CurriculumStructureConfig":
        """Create configuration from environment variables."""
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
            gemini_temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.1")),
            gemini_max_output_tokens=int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "8192")),
            use_fallback_regex=os.getenv("USE_FALLBACK_REGEX", "true").lower() == "true",
            fallback_confidence_threshold=float(os.getenv("FALLBACK_CONFIDENCE_THRESHOLD", "0.7")),
            min_section_length=int(os.getenv("MIN_SECTION_LENGTH", "10")),
            max_section_length=int(os.getenv("MAX_SECTION_LENGTH", "10000")),
            preserve_academic_structure=os.getenv("PRESERVE_ACADEMIC_STRUCTURE", "true").lower() == "true",
            output_format=os.getenv("OUTPUT_FORMAT", "json"),
            validate_schema=os.getenv("VALIDATE_SCHEMA", "true").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE"),
        )