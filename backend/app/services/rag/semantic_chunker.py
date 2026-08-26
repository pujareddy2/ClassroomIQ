from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass(slots=True)
class ParsedChunk:
    chunk_index: int
    section_title: Optional[str]
    page_number: Optional[int]
    chunk_text: str
    word_count: int
    token_count: int


# Patterns for heading detection (e.g. "Chapter 1: ...", "1.2 Introduction", "SECTION A", "UNIT I - ...")
_HEADING_PATTERNS = [
    re.compile(r"^\s*(?:CHAPTER|UNIT|MODULE|SECTION|PART)[\s:]+[IVXLCDM\d]*[\.:\s-]?\s*(.*)$", re.IGNORECASE),
    re.compile(r"^\s*\d+\.\d+\s+(.*)$"),
    re.compile(r"^\s*[A-Z\s]{4,60}$"),
]

# Page break pattern (e.g., "--- PAGE 5 ---" or form feed)
_PAGE_BREAK_RE = re.compile(r"(?:---\s*PAGE\s*(\d+)\s*---|^\s*\f\s*)", re.IGNORECASE | re.MULTILINE)


class SemanticChunker:
    """
    Splits reference document text into optimal overlapping academic chunks
    while tracking section headings and page numbers.
    """

    def __init__(
        self,
        target_chunk_words: int = 350,
        min_chunk_words: int = 20,
        overlap_words: int = 30,
        words_per_page_estimate: int = 350,
    ) -> None:
        self.target_chunk_words = target_chunk_words
        self.min_chunk_words = min_chunk_words
        self.overlap_words = overlap_words
        self.words_per_page_estimate = words_per_page_estimate

    def _is_heading(self, line: str) -> Optional[str]:
        stripped = line.strip()
        if not stripped or len(stripped) < 3 or len(stripped) > 100:
            return None
        if stripped.endswith((".", ";", ",")):
            return None
        for pat in _HEADING_PATTERNS:
            match = pat.match(stripped)
            if match:
                return stripped
        return None

    def chunk_text(self, text: str, document_title: Optional[str] = None) -> List[ParsedChunk]:
        if not text or not text.strip():
            return []

        lines = text.splitlines()
        chunks: List[ParsedChunk] = []
        
        current_section = document_title or "General Section"
        current_page = 1
        cumulative_word_count = 0

        paragraphs: List[tuple[str, Optional[str], int]] = []
        
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Check page break marker
            page_match = _PAGE_BREAK_RE.search(line_str)
            if page_match and page_match.group(1):
                try:
                    current_page = int(page_match.group(1))
                except ValueError:
                    pass
                continue

            # Check heading marker
            heading = self._is_heading(line_str)
            if heading:
                current_section = heading

            words = line_str.split()
            cumulative_word_count += len(words)

            inferred_page = max(1, (cumulative_word_count // self.words_per_page_estimate) + 1) if current_page == 1 else current_page
            paragraphs.append((line_str, current_section, inferred_page))

        # Build chunks with section-boundary awareness & overlapping window
        chunk_words: List[str] = []
        chunk_section: Optional[str] = None
        chunk_page: Optional[int] = None
        chunk_idx = 0

        for p_text, p_sec, p_pg in paragraphs:
            p_words = p_text.split()

            # Flush if section changes and accumulated words exist
            if chunk_section and p_sec != chunk_section and len(chunk_words) >= self.min_chunk_words:
                text_content = " ".join(chunk_words)
                token_est = int(len(chunk_words) * 1.3)
                chunks.append(
                    ParsedChunk(
                        chunk_index=chunk_idx,
                        section_title=chunk_section,
                        page_number=chunk_page or 1,
                        chunk_text=text_content,
                        word_count=len(chunk_words),
                        token_count=token_est,
                    )
                )
                chunk_idx += 1
                chunk_words = []
                chunk_section = p_sec
                chunk_page = p_pg

            if not chunk_section:
                chunk_section = p_sec
            if not chunk_page:
                chunk_page = p_pg

            chunk_words.extend(p_words)

            if len(chunk_words) >= self.target_chunk_words:
                text_content = " ".join(chunk_words)
                token_est = int(len(chunk_words) * 1.3)
                chunks.append(
                    ParsedChunk(
                        chunk_index=chunk_idx,
                        section_title=chunk_section,
                        page_number=chunk_page or 1,
                        chunk_text=text_content,
                        word_count=len(chunk_words),
                        token_count=token_est,
                    )
                )
                chunk_idx += 1
                
                # Retain overlap words
                if self.overlap_words > 0 and len(chunk_words) > self.overlap_words:
                    chunk_words = chunk_words[-self.overlap_words:]
                else:
                    chunk_words = []

        # Flush final remaining chunk
        if chunk_words and (len(chunk_words) >= self.min_chunk_words or not chunks):
            text_content = " ".join(chunk_words)
            token_est = int(len(chunk_words) * 1.3)
            chunks.append(
                ParsedChunk(
                    chunk_index=chunk_idx,
                    section_title=chunk_section or "General Section",
                    page_number=chunk_page or 1,
                    chunk_text=text_content,
                    word_count=len(chunk_words),
                    token_count=token_est,
                )
            )

        return chunks
