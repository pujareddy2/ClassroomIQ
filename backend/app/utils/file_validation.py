from __future__ import annotations

from datetime import date
import re
from pathlib import Path
from typing import Final

ALLOWED_EXTENSIONS: Final[set[str]] = {".pdf", ".docx", ".pptx", ".txt"}
ALLOWED_REFERENCE_TYPES: Final[set[str]] = {
    "REFERENCE_BOOK",
    "FACULTY_NOTES",
    "PPT",
    "LAB_MANUAL",
    "ASSIGNMENT",
    "QUESTION_BANK",
}
ALLOWED_SYLLABUS_TYPES: Final[set[str]] = {"SYLLABUS"}
DOCUMENT_FOLDER_MAP: Final[dict[str, str]] = {
    "SYLLABUS": "syllabus",
    "REFERENCE_BOOK": "reference_books",
    "FACULTY_NOTES": "faculty_notes",
    "PPT": "ppt",
    "LAB_MANUAL": "lab_manuals",
    "ASSIGNMENT": "assignments",
    "QUESTION_BANK": "question_banks",
}


class UploadValidationError(ValueError):
    """Base upload validation error."""


class UnsupportedFileTypeError(UploadValidationError):
    """Raised when file extension is not allowed."""


class FileTooLargeError(UploadValidationError):
    """Raised when file size exceeds configured maximum."""


class InvalidDocumentTypeError(UploadValidationError):
    """Raised when the document type is not allowed for the endpoint."""


class MissingMetadataError(UploadValidationError):
    """Raised when required metadata is missing or empty."""


def normalize_document_type(document_type: str) -> str:
    return document_type.strip().upper()


def validate_document_type(document_type: str, allowed_types: set[str]) -> str:
    normalized_type = normalize_document_type(document_type)
    if normalized_type not in allowed_types:
        raise InvalidDocumentTypeError(
            f"Unsupported document type '{document_type}'. Allowed types: {', '.join(sorted(allowed_types))}"
        )
    return normalized_type


def validate_file_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{extension or '[no extension]'}'. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return extension


def validate_file_size(file_size: int, max_file_size_bytes: int) -> None:
    if file_size > max_file_size_bytes:
        raise FileTooLargeError(
            f"File is too large. Maximum allowed size is {max_file_size_bytes} bytes."
        )


def sanitize_filename(filename: str) -> str:
    stem = Path(filename).stem
    suffix = Path(filename).suffix.lower()
    cleaned_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-")
    if not cleaned_stem:
        cleaned_stem = "document"
    return f"{cleaned_stem}{suffix}"


def parse_academic_year_dates(academic_year: str) -> tuple[date, date]:
    normalized = academic_year.strip()
    if not re.fullmatch(r"\d{4}-\d{4}", normalized):
        raise ValueError("Academic year must be formatted YYYY-YYYY")

    start_year, end_year = normalized.split("-")
    start = date(int(start_year), 1, 1)
    end = date(int(end_year), 12, 31)
    return start, end


def normalize_semester(semester_value: str) -> int:
    normalized = semester_value.strip().lower()
    normalized = re.sub(r"[^0-9a-z]+", " ", normalized)
    normalized = normalized.strip()

    if normalized.isdigit():
        semester_int = int(normalized)
    else:
        ordinal_map = {
            "first": 1,
            "1st": 1,
            "second": 2,
            "2nd": 2,
            "third": 3,
            "3rd": 3,
            "fourth": 4,
            "4th": 4,
            "fifth": 5,
            "5th": 5,
            "sixth": 6,
            "6th": 6,
            "seventh": 7,
            "7th": 7,
            "eighth": 8,
            "8th": 8,
        }
        semester_int = None
        for token in normalized.split():
            if token in ordinal_map:
                semester_int = ordinal_map[token]
                break
        if semester_int is None:
            match = re.search(r"(\d+)", normalized)
            if match:
                semester_int = int(match.group(1))

    if semester_int is None or semester_int < 1 or semester_int > 8:
        raise ValueError("Semester must be between 1 and 8")

    return semester_int
