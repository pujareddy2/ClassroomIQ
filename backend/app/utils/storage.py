from __future__ import annotations

import logging
from pathlib import Path

from app.utils.config import settings
from app.utils.file_validation import DOCUMENT_FOLDER_MAP, sanitize_filename

logger = logging.getLogger(__name__)


def get_storage_root() -> Path:
    settings.upload_root.mkdir(parents=True, exist_ok=True)
    return settings.upload_root


def get_document_folder(document_type: str) -> str:
    return DOCUMENT_FOLDER_MAP[document_type]


def build_document_directory(course_code: str, academic_year: str, semester: str, document_type: str) -> Path:
    root = get_storage_root()
    directory = root / sanitize_filename(course_code) / sanitize_filename(academic_year) / sanitize_filename(semester) / get_document_folder(document_type)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def make_unique_file_path(directory: Path, filename: str) -> Path:
    sanitized_name = sanitize_filename(filename)
    candidate = directory / sanitized_name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1
    while True:
        candidate = directory / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def save_document_bytes(directory: Path, filename: str, content: bytes) -> Path:
    destination = make_unique_file_path(directory, filename)
    destination.write_bytes(content)
    logger.info("Saved upload to %s", destination)
    return destination
