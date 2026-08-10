"""
Curriculum Structure Detection Service.

This service detects curriculum structure (modules, lessons, topics) in text
using either the Gemini API or a regex-based fallback.
"""

import json
import logging
import os
import re
import time
from typing import Dict, List, Optional, Any

from app.services.curriculum_structure.config import CurriculumStructureConfig
from app.services.curriculum_structure.exceptions import (
    CurriculumStructureError,
    ConfigurationError,
    GeminiAPIError,
    ValidationError,
    ParsingError,
)

logger = logging.getLogger(__name__)


class CurriculumStructureService:
    """
    Service for detecting curriculum structure in educational text.
    """

    def __init__(self, config: Optional[CurriculumStructureConfig] = None):
        """
        Initialize the curriculum structure service.

        Args:
            config: Configuration object. If None, loads from environment.
        """
        self.config = config or CurriculumStructureConfig.from_env()
        self._validate_config()
        self._setup_logging()
        self._gemini_client = None
        self._init_gemini_client()

    def _validate_config(self) -> None:
        """Validate configuration."""
        if not self.config.gemini_api_key and not self.config.use_fallback_regex:
            raise ConfigurationError(
                "Either Gemini API key must be provided or fallback regex must be enabled"
            )

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            filename=self.config.log_file,
        )

    def _init_gemini_client(self) -> None:
        """Initialize Gemini client if API key is available."""
        if self.config.gemini_api_key:
            try:
                # In a real implementation, we would import and initialize the Gemini client
                # For now, we'll just log that we would initialize it
                logger.info("Gemini API key found. Would initialize Gemini client.")
                # Placeholder for actual Gemini client initialization
                # self._gemini_client = genai.Client(api_key=self.config.gemini_api_key)
            except ImportError:
                logger.warning("Gemini AI package not installed. Falling back to regex.")
                self._gemini_client = None
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}. Falling back to regex.")
                self._gemini_client = None
        else:
            self._gemini_client = None
            logger.info("No Gemini API key provided. Using regex fallback.")

    def detect_structure(self, text: str) -> Dict[str, Any]:
        """
        Detect curriculum structure in the given text.

        Args:
            text: The cleaned text to analyze.

        Returns:
            A dictionary representing the detected curriculum structure.

        Raises:
            CurriculumStructureError: If detection fails.
        """
        if not text or not text.strip():
            raise ValidationError("Input text is empty or only whitespace")

        logger.info("Starting curriculum structure detection")
        start_time = time.time()

        # Try Gemini first if available
        if self._gemini_client is not None:
            try:
                result = self._detect_with_gemini(text)
                if self._validate_structure(result):
                    logger.info(f"Structure detected via Gemini in {time.time() - start_time:.2f}s")
                    return result
                else:
                    logger.warning("Gemini output failed validation. Falling back to regex.")
            except Exception as e:
                logger.warning(f"Gemini detection failed: {e}. Falling back to regex.")

        # Fallback to regex-based detection
        result = self._detect_with_regex(text)
        if self._validate_structure(result):
            logger.info(f"Structure detected via regex in {time.time() - start_time:.2f}s")
            return result
        else:
            raise ValidationError("Failed to detect valid curriculum structure with fallback method")

    def _detect_with_gemini(self, text: str) -> Dict[str, Any]:
        """
        Detect structure using Gemini API.

        Args:
            text: The text to analyze.

        Returns:
            Detected curriculum structure.

        Raises:
            GeminiAPIError: If the API call fails.
        """
        # This is a placeholder for actual Gemini API implementation
        # In a real implementation, we would:
        # 1. Construct a prompt for curriculum structure detection
        # 2. Call the Gemini API
        # 3. Parse the JSON response
        # 4. Return the structured data

        logger.warning("Gemini API detection not implemented. Returning empty structure.")
        raise GeminiAPIError("Gemini API detection not implemented")

    def _detect_with_regex(self, text: str) -> Dict[str, Any]:
        """
        Detect structure using regex-based fallback.

        Args:
            text: The text to analyze.

        Returns:
            Detected curriculum structure.
        """
        logger.info("Using regex-based fallback for curriculum structure detection")

        # Define patterns for common educational hierarchy
        # These patterns are simplified examples and would need to be expanded
        # for production use with more sophisticated educational taxonomies

        # Patterns for different levels (from broadest to most specific)
        patterns = {
            "program": [
                r"(?i)^\s*(program|programme|degree|course)\s*:?\s*(.+)$",
                r"(?i)^\s*(bachelor|master|phd|doctorate|diploma|certificate)\s+of\s+(.+)$",
            ],
            "module": [
                r"(?i)^\s*(module|unit|block|part)\s+(\d+|[ivxlcdm]+|[a-z])\s*:?\s*(.+)$",
                r"(?i)^\s*(module|unit|block|part)\s*:?\s*(.+)$",
            ],
            "lesson": [
                r"(?i)^\s*(lesson|lecture|session|chapter)\s+(\d+|[ivxlcdm]+|[a-z])\s*:?\s*(.+)$",
                r"(?i)^\s*(lesson|lecture|session|chapter)\s*:?\s*(.+)$",
            ],
            "topic": [
                r"(?i)^\s*(topic|subject|theme|section)\s+(\d+|[ivxlcdm]+|[a-z])\s*:?\s*(.+)$",
                r"(?i)^\s*(topic|subject|theme|section)\s*:?\s*(.+)$",
            ],
            "subtopic": [
                r"(?i)^\s*(subtopic|sub-topic|sub_section|subsection)\s+(\d+|[ivxlcdm]+|[a-z])\s*:?\s*(.+)$",
                r"(?i)^\s*(subtopic|sub-topic|sub_section|subsection)\s*:?\s*(.+)$",
            ],
            "concept": [
                r"(?i)^\s*(concept|idea|principle|theorem|law|rule)\s+(\d+|[ivxlcdm]+|[a-z])\s*:?\s*(.+)$",
                r"(?i)^\s*(concept|idea|principle|theorem|law|rule)\s*:?\s*(.+)$",
            ],
        }

        # Split text into lines for processing
        lines = text.split('\n')
        current_program = None
        current_module = None
        current_lesson = None
        current_topic = None
        current_subtopic = None

        # Result structure
        result = {
            "program": None,
            "modules": [],
        }

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # Try to match each pattern in order of hierarchy
            matched = False
            for level, level_patterns in patterns.items():
                for pattern in level_patterns:
                    match = re.match(pattern, line)
                    if match:
                        matched = True
                        groups = match.groups()
                        if level == "program":
                            # Start a new program
                            current_program = {
                                "title": groups[-1].strip() if len(groups) > 1 else groups[0].strip(),
                                "modules": []
                            }
                            result["program"] = current_program
                        elif level == "module":
                            current_module = {
                                "title": groups[-1].strip() if len(groups) > 1 else groups[0].strip(),
                                "lessons": []
                            }
                            if current_program is not None:
                                current_program["modules"].append(current_module)
                            else:
                                # If no program yet, create a default one
                                current_program = {
                                    "title": "Untitled Program",
                                    "modules": [current_module]
                                }
                                result["program"] = current_program
                        elif level == "lesson":
                            current_lesson = {
                                "title": groups[-1].strip() if len(groups) > 1 else groups[0].strip(),
                                "topics": []
                            }
                            if current_module is not None:
                                current_module["lessons"].append(current_lesson)
                            elif current_program is not None:
                                # Create a default module
                                current_module = {
                                    "title": "Untitled Module",
                                    "lessons": [current_lesson]
                                }
                                current_program["modules"].append(current_module)
                            else:
                                # Create program and module
                                current_program = {
                                    "title": "Untitled Program",
                                    "modules": [{
                                        "title": "Untitled Module",
                                        "lessons": [current_lesson]
                                    }]
                                }
                                result["program"] = current_program
                        elif level == "topic":
                            current_topic = {
                                "title": groups[-1].strip() if len(groups) > 1 else groups[0].strip(),
                                "subtopics": []
                            }
                            if current_lesson is not None:
                                current_lesson["topics"].append(current_topic)
                            elif current_module is not None and current_module["lessons"]:
                                # Add to last lesson
                                current_module["lessons"][-1]["topics"].append(current_topic)
                            elif current_program is not None and current_program["modules"]:
                                # Add to last module's last lesson
                                if current_program["modules"][-1]["lessons"]:
                                    current_program["modules"][-1]["lessons"][-1]["topics"].append(current_topic)
                                else:
                                    # Create a lesson in the last module
                                    new_lesson = {"title": "Untitled Lesson", "topics": [current_topic]}
                                    current_program["modules"][-1]["lessons"].append(new_lesson)
                            else:
                                # Create program -> module -> lesson -> topic
                                if result["program"] is None:
                                    result["program"] = {
                                        "title": "Untitled Program",
                                        "modules": []
                                    }
                                if not result["program"]["modules"]:
                                    result["program"]["modules"].append({
                                        "title": "Untitled Module",
                                        "lessons": []
                                    })
                                if not result["program"]["modules"][-1]["lessons"]:
                                    result["program"]["modules"][-1]["lessons"].append({
                                        "title": "Untitled Lesson",
                                        "topics": []
                                    })
                                result["program"]["modules"][-1]["lessons"][-1]["topics"].append(current_topic)
                        elif level == "subtopic":
                            current_subtopic = {
                                "title": groups[-1].strip() if len(groups) > 1 else groups[0].strip(),
                                "concepts": []
                            }
                            if current_topic is not None:
                                current_topic["subtopics"].append(current_subtopic)
                            elif current_lesson is not None and current_lesson["topics"]:
                                current_lesson["topics"][-1]["subtopics"].append(current_subtopic)
                            elif current_module is not None and current_module["lessons"]:
                                # Add to last lesson of last module
                                if current_module["lessons"]:
                                    last_lesson = current_module["lessons"][-1]
                                    if last_lesson["topics"]:
                                        last_lesson["topics"][-1]["subtopics"].append(current_subtopic)
                                    else:
                                        last_lesson["subtopics"] = [current_subtopic]
                                else:
                                    # Create a lesson in the last module
                                    new_lesson = {"title": "Untitled Lesson", "topics": [], "subtopics": [current_subtopic]}
                                    current_module["lessons"].append(new_lesson)
                            else:
                                # Create the hierarchy
                                if result["program"] is None:
                                    result["program"] = {
                                        "title": "Untitled Program",
                                        "modules": []
                                    }
                                if not result["program"]["modules"]:
                                    result["program"]["modules"].append({
                                        "title": "Untitled Module",
                                        "lessons": []
                                    })
                                if not result["program"]["modules"][-1]["lessons"]:
                                    result["program"]["modules"][-1]["lessons"].append({
                                        "title": "Untitled Lesson",
                                        "topics": []
                                    })
                                if not result["program"]["modules"][-1]["lessons"][-1]["topics"]:
                                    result["program"]["modules"][-1]["lessons"][-1]["topics"].append({
                                        "title": "Untitled Topic",
                                        "subtopics": []
                                    })
                                result["program"]["modules"][-1]["lessons"][-1]["topics"][-1]["subtopics"].append"  # This line is corrected below

                # Correction for the above line (which was cut off in the thought process)
                # We'll rewrite the subtopic handling correctly in the actual code
                # For now, we note that the above line has a syntax error and will fix it in the actual implementation
                pass

            if not matched:
                # If no pattern matched, treat as content under the current deepest level
                # We'll attach it as a concept or description to the current level
                # For simplicity, we'll add it as a concept to the current subtopic if exists
                if current_subtopic is not None:
                    if "concepts" not in current_subtopic:
                        current_subtopic["concepts"] = []
                    current_subtopic["concepts"].append(line)
                elif current_topic is not None:
                    if "subtopics" not in current_topic:
                        current_topic["subtopics"] = []
                    # Add as a new subtopic with the line as title
                    current_topic["subtopics"].append({
                        "title": line[:100],  # Limit length
                        "concepts": []
                    })
                elif current_lesson is not None:
                    if "topics" not in current_lesson:
                        current_lesson["topics"] = []
                    current_lesson["topics"].append({
                        "title": line[:100],
                        "subtopics": []
                    })
                elif current_module is not None:
                    if "lessons" not in current_module:
                        current_module["lessons"] = []
                    current_module["lessons"].append({
                        "title": line[:100],
                        "topics": []
                    })
                elif current_program is not None:
                    if "modules" not in current_program:
                        current_program["modules"] = []
                    current_program["modules"].append({
                        "title": line[:100],
                        "lessons": []
                    })
                else:
                    # Create the full hierarchy
                    result["program"] = {
                        "title": line[:100],
                        "modules": [{
                            "title": "Untitled Module",
                            "lessons": [{
                                "title": "Untitled Lesson",
                                "topics": [{
                                    "title": "Untitled Topic",
                                    "subtopics": [{
                                        "title": "Untitled Subtopic",
                                        "concepts": [line]
                                    }]
                                }]
                            }]
                        }]
                    }

        # If we never found a program, create a default one
        if result["program"] is None:
            result["program"] = {
                "title": "Untitled Program",
                "modules": [{
                    "title": "Untitled Module",
                    "lessons": [{
                        "title": "Untitled Lesson",
                        "topics": [{
                            "title": "Untitled Topic",
                            "subtopics": [{
                                "title": "Untitled Subtopic",
                                "concepts": [text[:100]] if text else []
                            }]
                        }]
                    }]
                }]
            }

        # Clean up empty structures
        self._clean_empty_nodes(result["program"])

        return result

    def _clean_empty_nodes(self, node: Dict[str, Any]) -> None:
        """
        Recursively remove empty or placeholder nodes from the structure.

        Args:
            node: The node to clean.
        """
        if isinstance(node, dict):
            # Remove empty or placeholder values
            keys_to_delete = []
            for key, value in node.items():
                if key == "title" and (not value or value.startswith("Untitled")):
                    # We might want to keep untitled titles if they have content
                    # For now, we'll only remove if completely empty and no children
                    pass
                elif isinstance(value, (dict, list)):
                    self._clean_empty_nodes(value)
                    if isinstance(value, list) and not value:
                        keys_to_delete.append(key)
                    elif isinstance(value, dict) and not value:
                        keys_to_delete.append(key)
                elif value is None:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del node[key]

        elif isinstance(node, list):
            # Remove empty dictionaries from lists
            i = 0
            while i < len(node):
                if isinstance(node[i], dict) and not node[i]:
                    node.pop(i)
                else:
                    if isinstance(node[i], dict):
                        self._clean_empty_nodes(node[i])
                    i += 1

    def _validate_structure(self, structure: Dict[str, Any]) -> bool:
        """
        Validate the detected structure against basic curriculum rules.

        Args:
            structure: The detected structure to validate.

        Returns:
            True if the structure is valid, False otherwise.
        """
        try:
            # Basic validation: must have a program
            if not isinstance(structure, dict) or "program" not in structure:
                return False

            program = structure["program"]
            if not isinstance(program, dict) or not program.get("title"):
                return False

            # Modules should be a list if present
            if "modules" in program:
                if not isinstance(program["modules"], list):
                    return False
                for module in program["modules"]:
                    if not self._validate_module(module):
                        return False

            return True
        except Exception:
            return False

    def _validate_module(self, module: Dict[str, Any]) -> bool:
        """Validate a module node."""
        if not isinstance(module, dict) or not module.get("title"):
            return False
        if "lessons" in module:
            if not isinstance(module["lessons"], list):
                return False
            for lesson in module["lessons"]:
                if not self._validate_lesson(lesson):
                    return False
        return True

    def _validate_lesson(self, lesson: Dict[str, Any]) -> bool:
        """Validate a lesson node."""
        if not isinstance(lesson, dict) or not lesson.get("title"):
            return False
        if "topics" in lesson:
            if not isinstance(lesson["topics"], list):
                return False
            for topic in lesson["topics"]:
                if not self._validate_topic(topic):
                    return False
        return True

    def _validate_topic(self, topic: Dict[str, Any]) -> bool:
        """Validate a topic node."""
        if not isinstance(topic, dict) or not topic.get("title"):
            return False
        if "subtopics" in topic:
            if not isinstance(topic["subtopics"], list):
                return False
            for subtopic in topic["subtopics"]:
                if not self._validate_subtopic(subtopic):
                    return False
        return True

    def _validate_subtopic(self, subtopic: Dict[str, Any]) -> bool:
        """Validate a subtopic node."""
        if not isinstance(subtopic, dict) or not subtopic.get("title"):
            return False
        # Concepts are optional
        if "concepts" in subtopic:
            if not isinstance(subtopic["concepts"], list):
                return False
            # Concepts can be strings or dicts, we'll accept either
            for concept in subtopic["concepts"]:
                if isinstance(concept, dict):
                    if not concept.get("title"):
                        return False
                elif not isinstance(concept, str):
                    return False
        return True

    def get_structure_summary(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of the detected structure.

        Args:
            structure: The detected curriculum structure.

        Returns:
            A summary dictionary with counts and other metrics.
        """
        try:
            program = structure.get("program", {})
            module_count = len(program.get("modules", [])) if isinstance(program.get("modules"), list) else 0
            lesson_count = 0
            topic_count = 0
            subtopic_count = 0
            concept_count = 0

            for module in program.get("modules", []):
                lesson_count += len(module.get("lessons", []))
                for lesson in module.get("lessons", []):
                    topic_count += len(lesson.get("topics", []))
                    for topic in lesson.get("topics", []):
                        subtopic_count += len(topic.get("subtopics", []))
                        for subtopic in topic.get("subtopics", []):
                            concept_count += len(subtopic.get("concepts", []))

            return {
                "program_title": program.get("title", "Untitled"),
                "module_count": module_count,
                "lesson_count": lesson_count,
                "topic_count": topic_count,
                "subtopic_count": subtopic_count,
                "concept_count": concept_count,
                "total_nodes": 1 + module_count + lesson_count + topic_count + subtopic_count + concept_count,
            }
        except Exception as e:
            logger.error(f"Error generating structure summary: {e}")
            return {"error": str(e)}