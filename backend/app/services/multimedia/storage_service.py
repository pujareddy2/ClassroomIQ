"""
Storage service for Multimedia & Lecture Capture.
Organizes uploaded media, stream chunks, extracted audio, and slide frames per session.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Final, List, Optional
from uuid import UUID

from app.utils.config import settings

logger = logging.getLogger(__name__)

ALLOWED_VIDEO_EXTENSIONS: Final[set[str]] = {".mp4", ".webm", ".mkv", ".mov", ".avi"}
ALLOWED_AUDIO_EXTENSIONS: Final[set[str]] = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}
ALLOWED_SLIDE_EXTENSIONS: Final[set[str]] = {".pptx", ".ppt", ".pdf"}


def sanitize_filename(filename: str) -> str:
    """Sanitizes filename for safe filesystem storage."""
    stem = Path(filename).stem
    suffix = Path(filename).suffix.lower()
    cleaned_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-")
    if not cleaned_stem:
        cleaned_stem = "file"
    return f"{cleaned_stem}{suffix}"


class MultimediaStorageService:
    """Manages disk storage for lecture sessions, recordings, slides, and frames."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or (settings.upload_root / "sessions")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_session_dir(self, session_id: UUID) -> Path:
        """Returns the root directory for a specific lecture session."""
        session_path = self.base_dir / str(session_id)
        session_path.mkdir(parents=True, exist_ok=True)
        return session_path

    def init_session_dir(self, session_id: UUID) -> dict[str, Path]:
        """Initializes and returns all subdirectories for a session."""
        root = self.get_session_dir(session_id)
        dirs = {
            "root": root,
            "raw": root / "raw",
            "audio": root / "audio",
            "frames": root / "frames",
            "slides": root / "slides",
            "chunks": root / "chunks",
        }
        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)
        return dirs

    def get_session_paths(self, session_id: UUID) -> dict[str, Path]:
        """Retrieves existing subdirectories for a session without recreating if not needed."""
        return self.init_session_dir(session_id)

    def save_chunk(self, session_id: UUID, chunk_index: int, chunk_bytes: bytes) -> tuple[Path, int]:
        """Saves an incoming live recording stream chunk."""
        dirs = self.init_session_dir(session_id)
        chunk_file = dirs["chunks"] / f"chunk_{chunk_index:06d}.part"
        chunk_file.write_bytes(chunk_bytes)
        logger.debug("Saved session %s chunk %d (%d bytes)", session_id, chunk_index, len(chunk_bytes))
        return chunk_file, len(chunk_bytes)

    def get_chunks_count(self, session_id: UUID) -> int:
        """Returns total number of chunks received for a session."""
        dirs = self.init_session_dir(session_id)
        return len(list(dirs["chunks"].glob("chunk_*.part")))

    def assemble_chunks(self, session_id: UUID, output_filename: str = "recorded_lecture.webm") -> Path:
        """Concatenates all stream chunks in order into a single media file in the raw directory."""
        dirs = self.init_session_dir(session_id)
        chunks = sorted(dirs["chunks"].glob("chunk_*.part"))
        if not chunks:
            raise FileNotFoundError(f"No stream chunks found for session {session_id}")

        dest = dirs["raw"] / sanitize_filename(output_filename)
        with open(dest, "wb") as outfile:
            for chunk_file in chunks:
                with open(chunk_file, "rb") as infile:
                    outfile.write(infile.read())

        logger.info("Assembled %d chunks for session %s into %s", len(chunks), session_id, dest)
        return dest

    def save_raw_file(
        self,
        session_id: UUID,
        filename: str,
        content: bytes,
        category: str = "raw",
    ) -> Path:
        """Saves a file into the specified session directory (raw, slides, etc.)."""
        dirs = self.init_session_dir(session_id)
        target_dir = dirs.get(category, dirs["raw"])
        safe_name = sanitize_filename(filename)
        target_path = target_dir / safe_name
        target_path.write_bytes(content)
        logger.info("Saved %s to %s", safe_name, target_path)
        return target_path

    def list_slide_frames(self, session_id: UUID) -> List[Path]:
        """Returns all slide image previews generated for a session, sorted numerically."""
        dirs = self.init_session_dir(session_id)
        return sorted(
            [f for f in dirs["slides"].glob("slide_*.png")] + [f for f in dirs["slides"].glob("slide_*.jpg")],
            key=lambda p: p.stem,
        )

    def list_video_frames(self, session_id: UUID) -> List[Path]:
        """Returns all extracted video keyframe images for a session, sorted numerically."""
        dirs = self.init_session_dir(session_id)
        return sorted(
            [f for f in dirs["frames"].glob("frame_*.jpg")] + [f for f in dirs["frames"].glob("frame_*.png")],
            key=lambda p: p.stem,
        )

    def delete_session_dir(self, session_id: UUID) -> bool:
        """Deletes all disk files and directories associated with a session."""
        import shutil
        session_path = self.base_dir / str(session_id)
        if session_path.exists():
            shutil.rmtree(session_path, ignore_errors=True)
            logger.info("Deleted session disk directory: %s", session_path)
            return True
        return False

