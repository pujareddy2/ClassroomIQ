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
from app.services.curriculum_structure.utils.logger import setup_logger, get_logger
from app.services.curriculum_structure.utils.regex_patterns import CurriculumRegexPatterns
from app.services.curriculum_structure.utils.prompt_templates import PromptTemplates as PT  # Avoid name conflict

# Initialize logger
logger = get_logger(__name__)


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
        # Logging is already set up by the logger module, but we can adjust levels
        logging.getLogger().setLevel(getattr(logging, self.config.log_level.upper(), logging.INFO))

    def _init_gemini_client(self) -> None:
        """Initialize Gemini client if API key is available."""
        if self.config.gemini_api_key:
            try:
                # In a real implementation, we would import and initialize the Gemini client
                # For example: import google.generativeai as genai
                # genai.configure(api_key=self.config.gemini_api_key)
                # self._gemini_client = genai.GenerativeModel(self.config.gemini_model)
                logger.info("Gemini API key found. Would initialize Gemini client.")
                # Placeholder - in reality we would set up the client here
                self._gemini_client = None  # We'll keep it as None and use fallback for now
            except ImportError:
                logger.warning("Google Generative AI package not installed. Falling back to regex.")
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

        # Preprocess text to remove headers/footers if configured
        processed_text = self._preprocess_text(text)

        # Try Gemini first if available
        if self._gemini_client is not None and self.config.gemini_api_key:
            try:
                result = self._detect_with_gemini(processed_text)
                if self._validate_structure(result):
                    logger.info(f"Structure detected via Gemini in {time.time() - start_time:.2f}s")
                    return self._postprocess_structure(result)
                else:
                    logger.warning("Gemini output failed validation. Falling back to regex.")
            except Exception as e:
                logger.warning(f"Gemini detection failed: {e}. Falling back to regex.")

        # Fallback to regex-based detection
        result = self._detect_with_regex(processed_text)
        if self._validate_structure(result):
            logger.info(f"Structure detected via regex in {time.time() - start_time:.2f}s")
            return self._postprocess_structure(result)
        else:
            raise ValidationError("Failed to detect valid curriculum structure with fallback method")

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text by removing headers, footers, and other non-content elements.

        Args:
            text: The raw text.

        Returns:
            Preprocessed text.
        """
        if not self.config.preserve_academic_structure:
            # If we're not preserving academic structure, we might want to clean more aggressively
            pass

        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Skip empty lines
            if not line.strip():
                cleaned_lines.append(line)
                continue

            # Check if line should be ignored (page numbers, headers, etc.)
            from app.services.curriculum_structure.utils.regex_patterns import CurriculumRegexPatterns
            if CurriculumRegexPatterns.should_ignore_line(line):
                logger.debug(f"Ignoring line: {line[:50]}...")
                continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

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
        # In a real implementation:
        # 1. Format the prompt using PromptTemplates.get_curriculum_prompt(text)
        # 2. Call the Gemini API with the prompt
        # 3. Parse the JSON response
        # 4. Optionally refine the result with a second call

        logger.warning("Gemini API detection not fully implemented. Returning empty structure.")
        # For now, we'll return an empty structure to trigger fallback
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

        # Lines to process
        lines = text.split('\n')

        # Initialize structure
        structure = {
            "program": {
                "title": "Untitled Program",
                "description": "",
                "modules": []
            }
        }

        # Current context tracking
        current_program = structure["program"]
        current_module = None
        current_lesson = None
        current_topic = None
        current_subtopic = None

        # Check if the text contains any structural headers (other than program)
        has_structure = False
        for line in lines:
            if not line.strip():
                continue
            from app.services.curriculum_structure.utils.regex_patterns import CurriculumRegexPatterns
            if CurriculumRegexPatterns.should_ignore_line(line):
                continue
            matched = self._try_match_hierarchy(line, {}, {}, {}, {}, {})
            if matched:
                has_structure = True
                break

        # Process each line
        first_line_processed = False
        for line_num, line in enumerate(lines, 1):
            line = line.rstrip()  # Remove trailing whitespace but keep leading for indentation analysis
            if not line.strip():
                # Empty line - preserve as potential separator
                continue

            # Skip lines that should be ignored (but we already preprocessed, so double-check)
            from app.services.curriculum_structure.utils.regex_patterns import CurriculumRegexPatterns
            if CurriculumRegexPatterns.should_ignore_line(line):
                continue

            # Try to match hierarchical patterns
            matched = self._try_match_hierarchy(line, current_program,
                                               current_module, current_lesson,
                                               current_topic, current_subtopic)

            if matched:
                current_program, current_module, current_lesson, current_topic, current_subtopic = matched
                first_line_processed = True
            else:
                # Treat as content - add to current deepest level
                if has_structure and not first_line_processed and current_program["title"] == "Untitled Program":
                    current_program["title"] = line.strip()
                    first_line_processed = True
                else:
                    self._add_content_to_current_level(line, current_program, current_module,
                                                     current_lesson, current_topic, current_subtopic)
                    first_line_processed = True

        # Clean up empty containers
        self._cleanup_empty_containers(structure["program"])

        return structure

    def _try_match_hierarchy(self, line: str, current_program: dict, current_module: dict,
                           current_lesson: dict, current_topic: dict, current_subtopic: dict):
        """
        Try to match a line against hierarchical patterns.

        Returns updated context tuple or None if no match.
        """
        # Patterns for different levels (from most specific to least specific for proper nesting)
        patterns = [
            # Concept patterns
            (r'(?i)^\s*(concept|idea|principle|theorem|law|rule)\s+([\d\.\-A-Za-z]+)\s*[:.-]?\s*(.+)$', 'concept'),
            (r'(?i)^\s*(concept|idea|principle|theorem|law|rule)\s*[:.-]?\s*(.+)$', 'concept'),
            # Subtopic patterns
            (r'(?i)^\s*(subtopic|sub-topic|subsection)\s+([\d\.\-A-Za-z]+)\s*[:.-]?\s*(.+)$', 'subtopic'),
            (r'(?i)^\s*(subtopic|sub-topic|subsection)\s*[:.-]?\s*(.+)$', 'subtopic'),
            # Topic patterns
            (r'(?i)^\s*(topic|subject|theme|section)\s+([\d\.\-A-Za-z]+)\s*[:.-]?\s*(.+)$', 'topic'),
            (r'(?i)^\s*(topic|subject|theme|section)\s*[:.-]?\s*(.+)$', 'topic'),
            # Lesson patterns
            (r'(?i)^\s*(lesson|lecture|session|chapter)\s+([\d\.\-A-Za-z]+)\s*[:.-]?\s*(.+)$', 'lesson'),
            (r'(?i)^\s*(lesson|lecture|session|chapter)\s*[:.-]?\s*(.+)$', 'lesson'),
            # Module patterns
            (r'(?i)^\s*(module|unit|block|part)\s+([\d\.\-A-Za-z]+)\s*[:.-]?\s*(.+)$', 'module'),
            (r'(?i)^\s*(module|unit|block|part)\s*[:.-]?\s*(.+)$', 'module'),
            # Program patterns
            (r'(?i)^\s*(program|programme|degree|course)\s+([\d\.\-A-Za-z]+)\s*[:.-]?\s*(.+)$', 'program'),
            (r'(?i)^\s*(program|programme|degree|course)\s*[:.-]?\s*(.+)$', 'program'),
        ]

        for pattern, level in patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                title = groups[-1].strip()  # Last group is always the title
                # Clean up title (remove extra spaces, etc.)
                title = re.sub(r'\s+', ' ', title).strip()

                if not title:
                    continue

                # Update context based on level
                if level == 'program':
                    # New program - reset everything
                    new_program = {
                        "title": title,
                        "description": "",
                        "modules": []
                    }
                    return (new_program, None, None, None, None)

                elif level == 'module':
                    # New module - reset lesson and below
                    new_module = {
                        "title": title,
                        "description": "",
                        "lessons": []
                    }
                    if current_program:
                        current_program["modules"].append(new_module)
                        return (current_program, new_module, None, None, None)
                    else:
                        # No program yet - create a default one
                        new_program = {
                            "title": "Untitled Program",
                            "description": "",
                            "modules": [new_module]
                        }
                        return (new_program, new_module, None, None, None)

                elif level == 'lesson':
                    # New lesson - reset topic and below
                    new_lesson = {
                        "title": title,
                        "description": "",
                        "topics": []
                    }
                    if current_module:
                        current_module["lessons"].append(new_lesson)
                        return (current_program, current_module, new_lesson, None, None)
                    elif current_program:
                        # Create a default module
                        new_module = {
                            "title": "Untitled Module",
                            "description": "",
                            "lessons": [new_lesson]
                        }
                        current_program["modules"].append(new_module)
                        return (current_program, new_module, new_lesson, None, None)
                    else:
                        # Create program and module
                        new_program = {
                            "title": "Untitled Program",
                            "description": "",
                            "modules": [{
                                "title": "Untitled Module",
                                "description": "",
                                "lessons": [new_lesson]
                            }]
                        }
                        return (new_program, new_program["modules"][0], new_lesson, None, None)

                elif level == 'topic':
                    # New topic - reset subtopic and below
                    new_topic = {
                        "title": title,
                        "description": "",
                        "subtopics": []
                    }
                    if current_lesson:
                        current_lesson["topics"].append(new_topic)
                        return (current_program, current_module, current_lesson, new_topic, None)
                    elif current_module and current_module["lessons"]:
                        # Add to last lesson
                        last_lesson = current_module["lessons"][-1]
                        last_lesson["topics"].append(new_topic)
                        return (current_program, current_module, current_lesson, new_topic, None)
                    elif current_program and current_program["modules"]:
                        # Add to last module's last lesson
                        last_module = current_program["modules"][-1]
                        if last_module["lessons"]:
                            last_lesson = last_module["lessons"][-1]
                            last_lesson["topics"].append(new_topic)
                            return (current_program, current_module, current_lesson, new_topic, None)
                        else:
                            # Create a lesson in the last module
                            new_lesson = {
                                "title": "Untitled Lesson",
                                "description": "",
                                "topics": [new_topic]
                            }
                            last_module["lessons"].append(new_lesson)
                            return (current_program, current_module, new_lesson, new_topic, None)
                    else:
                        # Create the hierarchy
                        new_program = {
                            "title": "Untitled Program",
                            "description": "",
                            "modules": [{
                                "title": "Untitled Module",
                                "description": "",
                                "lessons": [{
                                    "title": "Untitled Lesson",
                                    "description": "",
                                    "topics": [new_topic]
                                }]
                            }]
                        }
                        return (new_program, new_program["modules"][0],
                              new_program["modules"][0]["lessons"][0], new_topic, None)

                elif level == 'subtopic':
                    # New subtopic - reset concept and below
                    new_subtopic = {
                        "title": title,
                        "description": "",
                        "concepts": []
                    }
                    if current_topic:
                        current_topic["subtopics"].append(new_subtopic)
                        return (current_program, current_module, current_lesson, current_topic, new_subtopic)
                    elif current_lesson and current_lesson["topics"]:
                        # Add to last topic
                        last_topic = current_lesson["topics"][-1]
                        last_topic["subtopics"].append(new_subtopic)
                        return (current_program, current_module, current_lesson, current_topic, new_subtopic)
                    elif current_module and current_module["lessons"]:
                        # Add to last lesson's last topic
                        last_lesson = current_module["lessons"][-1]
                        if last_lesson["topics"]:
                            last_topic = last_lesson["topics"][-1]
                            last_topic["subtopics"].append(new_subtopic)
                            return (current_program, current_module, current_lesson, current_topic, new_subtopic)
                        else:
                            # Create a topic in the last lesson
                            new_topic = {
                                "title": "Untitled Topic",
                                "description": "",
                                "subtopics": [new_subtopic]
                            }
                            last_lesson["topics"].append(new_topic)
                            return (current_program, current_module, current_lesson, current_topic, new_subtopic)
                    else:
                        # Create the hierarchy
                        new_program = {
                            "title": "Untitled Program",
                            "description": "",
                            "modules": [{
                                "title": "Untitled Module",
                                "description": "",
                                "lessons": [{
                                    "title": "Untitled Lesson",
                                    "description": "",
                                    "topics": [{
                                        "title": "Untitled Topic",
                                        "description": "",
                                        "subtopics": [new_subtopic]
                                    }]
                                }]
                            }]
                        }
                        return (new_program, new_program["modules"][0],
                              new_program["modules"][0]["lessons"][0],
                              new_program["modules"][0]["lessons"][0]["topics"][0], new_subtopic)

                elif level == 'concept':
                    # New concept - add to current subtopic
                    new_concept = {
                        "title": title,
                        "description": ""
                    }
                    if current_subtopic:
                        current_subtopic["concepts"].append(new_concept)
                        return (current_program, current_module, current_lesson, current_topic, current_subtopic)
                    elif current_topic and current_topic["subtopics"]:
                        # Add to last subtopic
                        last_subtopic = current_topic["subtopics"][-1]
                        last_subtopic["concepts"].append(new_concept)
                        return (current_program, current_module, current_lesson, current_topic, current_subtopic)
                    elif current_lesson and current_lesson["topics"]:
                        # Add to last topic's last subtopic
                        last_topic = current_lesson["topics"][-1]
                        if last_topic["subtopics"]:
                            last_subtopic = last_topic["subtopics"][-1]
                            last_subtopic["concepts"].append(new_concept)
                            return (current_program, current_module, current_lesson, current_topic, current_subtopic)
                        else:
                            # Create a subtopic in the last topic
                            new_subtopic = {
                                "title": "Untitled Subtopic",
                                "description": "",
                                "concepts": [new_concept]
                            }
                            last_topic["subtopics"].append(new_subtopic)
                            return (current_program, current_module, current_lesson, current_topic, new_subtopic)
                    else:
                        # Create the hierarchy down to concept
                        new_program = {
                            "title": "Untitled Program",
                            "description": "",
                            "modules": [{
                                "title": "Untitled Module",
                                "description": "",
                                "lessons": [{
                                    "title": "Untitled Lesson",
                                    "description": "",
                                    "topics": [{
                                        "title": "Untitled Topic",
                                        "description": "",
                                        "subtopics": [{
                                            "title": "Untitled Subtopic",
                                            "description": "",
                                            "concepts": [new_concept]
                                        }]
                                    }]
                                }]
                            }]
                        }
                        return (new_program, new_program["modules"][0],
                              new_program["modules"][0]["lessons"][0],
                              new_program["modules"][0]["lessons"][0]["topics"][0],
                              new_program["modules"][0]["lessons"][0]["topics"][0]["subtopics"][0])

        return None  # No pattern matched

    def _add_content_to_current_level(self, line: str, current_program: dict, current_module: dict,
                                    current_lesson: dict, current_topic: dict, current_subtopic: dict):
        """
        Add content line to the current deepest level in the hierarchy.
        """
        # Clean the line
        cleaned_line = ' '.join(line.split())  # Normalize whitespace
        if not cleaned_line:
            return

        # Add as a concept to the current subtopic if exists
        if current_subtopic is not None:
            if "content" not in current_subtopic:
                current_subtopic["content"] = []
            current_subtopic["content"].append(cleaned_line)
            return

        # Otherwise add to current topic
        if current_topic is not None:
            if "content" not in current_topic:
                current_topic["content"] = []
            current_topic["content"].append(cleaned_line)
            return

        # Otherwise add to current lesson
        if current_lesson is not None:
            if "content" not in current_lesson:
                current_lesson["content"] = []
            current_lesson["content"].append(cleaned_line)
            return

        # Otherwise add to current module
        if current_module is not None:
            if "content" not in current_module:
                current_module["content"] = []
            current_module["content"].append(cleaned_line)
            return

        # Otherwise add to current program
        if current_program is not None:
            if "content" not in current_program:
                current_program["content"] = []
            current_program["content"].append(cleaned_line)
            return

    def _cleanup_empty_containers(self, node: dict):
        """
        Recursively remove empty containers from the structure.
        """
        if isinstance(node, dict):
            # Remove empty string fields that are not essential
            keys_to_check = ["description", "content"]
            for key in keys_to_check:
                if key in node and not node[key]:
                    del node[key]

            # Process nested structures
            if "modules" in node:
                node["modules"] = [m for m in node["modules"] if m]  # Remove empty modules
                for module in node["modules"]:
                    self._cleanup_empty_containers(module)

            if "lessons" in node:
                node["lessons"] = [l for l in node["lessons"] if l]  # Remove empty lessons
                for lesson in node["lessons"]:
                    self._cleanup_empty_containers(lesson)

            if "topics" in node:
                node["topics"] = [t for t in node["topics"] if t]  # Remove empty topics
                for topic in node["topics"]:
                    self._cleanup_empty_containers(topic)

            if "subtopics" in node:
                node["subtopics"] = [s for s in node["subtopics"] if s]  # Remove empty subtopics
                for subtopic in node["subtopics"]:
                    self._cleanup_empty_containers(subtopic)

            if "concepts" in node:
                node["concepts"] = [c for c in node["concepts"] if c]  # Remove empty concepts
                for concept in node["concepts"]:
                    self._cleanup_empty_containers(concept)

        elif isinstance(node, list):
            # Remove empty items from list
            i = 0
            while i < len(node):
                if isinstance(node[i], dict) and not node[i]:
                    node.pop(i)
                elif isinstance(node[i], list) and not node[i]:
                    node.pop(i)
                else:
                    if isinstance(node[i], (dict, list)):
                        self._cleanup_empty_containers(node[i])
                    i += 1

    def _validate_structure(self, structure: Dict[str, Any]) -> bool:
        """
        Validate that the structure meets basic requirements.

        Args:
            structure: The structure to validate.

        Returns:
            True if valid, False otherwise.
        """
        if not isinstance(structure, dict):
            return False

        # Must have a program
        if "program" not in structure or not isinstance(structure["program"], dict):
            return False

        program = structure["program"]
        if "title" not in program or not isinstance(program["title"], str):
            return False

        # Modules should be a list if present
        if "modules" in program and not isinstance(program["modules"], list):
            return False

        # Validate each module recursively
        return self._validate_module_structure(program.get("modules", []))

    def _validate_module_structure(self, modules: list) -> bool:
        """Validate module structure."""
        for module in modules:
            if not isinstance(module, dict):
                return False
            if "title" not in module or not isinstance(module["title"], str):
                return False
            if "lessons" in module and not isinstance(module["lessons"], list):
                return False
            if not self._validate_lesson_structure(module.get("lessons", [])):
                return False
        return True

    def _validate_lesson_structure(self, lessons: list) -> bool:
        """Validate lesson structure."""
        for lesson in lessons:
            if not isinstance(lesson, dict):
                return False
            if "title" not in lesson or not isinstance(lesson["title"], str):
                return False
            if "topics" in lesson and not isinstance(lesson["topics"], list):
                return False
            if not self._validate_topic_structure(lesson.get("topics", [])):
                return False
        return True

    def _validate_topic_structure(self, topics: list) -> bool:
        """Validate topic structure."""
        for topic in topics:
            if not isinstance(topic, dict):
                return False
            if "title" not in topic or not isinstance(topic["title"], str):
                return False
            if "subtopics" in topic and not isinstance(topic["subtopics"], list):
                return False
            if not self._validate_subtopic_structure(topic.get("subtopics", [])):
                return False
        return True

    def _validate_subtopic_structure(self, subtopics: list) -> bool:
        """Validate subtopic structure."""
        for subtopic in subtopics:
            if not isinstance(subtopic, dict):
                return False
            if "title" not in subtopic or not isinstance(subtopic["title"], str):
                return False
            if "concepts" in subtopic and not isinstance(subtopic["concepts"], list):
                return False
            if not self._validate_concept_structure(subtopic.get("concepts", [])):
                return False
        return True

    def _validate_concept_structure(self, concepts: list) -> bool:
        """Validate concept structure."""
        for concept in concepts:
            if not isinstance(concept, dict):
                return False
            if "title" not in concept or not isinstance(concept["title"], str):
                return False
        return True

    def _postprocess_structure(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-process the structure to ensure consistency and quality.

        Args:
            structure: The raw structure from detection.

        Returns:
            Post-processed structure.
        """
        # Ensure we have a program
        if "program" not in structure:
            structure["program"] = {
                "title": "Untitled Program",
                "modules": []
            }

        # Ensure program has required fields
        program = structure["program"]
        if "title" not in program:
            program["title"] = "Untitled Program"
        if "description" not in program:
            program["description"] = ""
        if "modules" not in program:
            program["modules"] = []

        # Process modules
        for module in program["modules"]:
            if "title" not in module:
                module["title"] = "Untitled Module"
            if "description" not in module:
                module["description"] = ""
            if "lessons" not in module:
                module["lessons"] = []

            # Process lessons
            for lesson in module["lessons"]:
                if "title" not in lesson:
                    lesson["title"] = "Untitled Lesson"
                if "description" not in lesson:
                    lesson["description"] = ""
                if "topics" not in lesson:
                    lesson["topics"] = []

                # Process topics
                for topic in lesson["topics"]:
                    if "title" not in topic:
                        topic["title"] = "Untitled Topic"
                    if "description" not in topic:
                        topic["description"] = ""
                    if "subtopics" not in topic:
                        topic["subtopics"] = []

                    # Process subtopics
                    for subtopic in topic["subtopics"]:
                        if "title" not in subtopic:
                            subtopic["title"] = "Untitled Subtopic"
                        if "description" not in subtopic:
                            subtopic["description"] = ""
                        if "concepts" not in subtopic:
                            subtopic["concepts"] = []

                        # Process concepts
                        for concept in subtopic["concepts"]:
                            if "title" not in concept:
                                concept["title"] = "Untitled Concept"
                            if "description" not in concept:
                                concept["description"] = ""

        return structure