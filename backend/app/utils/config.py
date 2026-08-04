from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parents[3]
_BACKEND_ROOT = _HERE.parents[2]

_dotenv_path = _PROJECT_ROOT / ".env"
if not _dotenv_path.exists():
    _dotenv_path = _BACKEND_ROOT / ".env"

load_dotenv(dotenv_path=str(_dotenv_path))


@dataclass(frozen=True, slots=True)
class UploadSettings:
    upload_root: Path
    max_file_size_mb: int

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


settings = UploadSettings(
    upload_root=Path(os.getenv("UPLOAD_ROOT", str(_PROJECT_ROOT / "uploads"))),
    max_file_size_mb=int(os.getenv("MAX_UPLOAD_SIZE_MB", "25")),
)
