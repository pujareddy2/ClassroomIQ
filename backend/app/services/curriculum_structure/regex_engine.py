"""
regex_engine.py

Responsible for scanning cleaned academic text and detecting structural academic markers
using predefined regex patterns from regex_patterns.py.
"""

import re
import time
import logging
import sys
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Ensure root is in path to import regex_patterns from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

# Import from the root regex_patterns.py
from regex_patterns import get_all_patterns

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Marker(BaseModel):
    marker_type: str
    marker_value: str
    marker_number: Optional[int] = None
    line_number: int
    character_start: int
    character_end: int
    confidence: float = 1.0
    matched_text: str

class DetectionResult(BaseModel):
    markers: List[Marker]
    warnings: List[str]

class RegexDetectionEngine:
    def __init__(self):
        self.patterns = get_all_patterns()
        logger.info("Regex patterns loaded.")

    def _extract_number(self, value: str) -> Optional[int]:
        # Simple extraction for now. Can be expanded to handle Roman numerals.
        nums = re.findall(r'\d+', value)
        if nums:
            return int(nums[0])
        return None

    def detect(self, text: str) -> DetectionResult:
        logger.info("Regex detection started.")
        start_time = time.time()

        markers = []
        warnings = []

        if not text:
            logger.warning("Empty document provided.")
            return DetectionResult(markers=[], warnings=["Empty document"])

        lines = text.splitlines()

        for line_num, line in enumerate(lines, 1):
            for marker_type, pattern in self.patterns.items():
                for match in re.finditer(pattern, line):
                    # Basic marker creation
                    marker = Marker(
                        marker_type=marker_type.upper(),
                        marker_value=match.group(),
                        marker_number=self._extract_number(match.group()),
                        line_number=line_num,
                        character_start=match.start(),
                        character_end=match.end(),
                        matched_text=match.group()
                    )
                    markers.append(marker)

        execution_time = time.time() - start_time
        logger.info(f"Regex detection completed in {execution_time:.4f} sec. Found {len(markers)} markers.")

        return DetectionResult(markers=markers, warnings=warnings)
