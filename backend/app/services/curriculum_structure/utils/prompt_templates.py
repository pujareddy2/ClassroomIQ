"""
Prompt templates for Gemini API calls.
"""

from typing import Dict, Any


class PromptTemplates:
    """Templates for prompting the Gemini model."""

    # Main prompt for curriculum structure detection
    CURRICULUM_STRUCTURE_PROMPT = """
You are an expert educational analyst specializing in curriculum design and instructional design.
Your task is to analyze the provided educational text and identify its hierarchical curriculum structure.

The structure should be organized in this hierarchy:
- Program (or Course, Degree, Programme)
  - Module (or Unit, Block, Part)
    - Lesson (or Lecture, Session, Chapter)
      - Topic (or Subject, Theme, Section)
        - Subtopic
          - Concept (or Idea, Principle, Theorem, Law, Rule)

For each level, extract:
1. The title/name of the component
2. A brief description if available (optional)
3. Any identified learning outcomes or objectives (optional)

Return the structure as a JSON object with the following format:
{{
  "program": {{
    "title": "Program Title",
    "description": "Program description if available",
    "modules": [
      {{
        "title": "Module Title",
        "description": "Module description if available",
        "lessons": [
          {{
            "title": "Lesson Title",
            "description": "Lesson description if available",
            "topics": [
              {{
                "title": "Topic Title",
                "description": "Topic description if available",
                "subtopics": [
                  {{
                    "title": "Subtopic Title",
                    "description": "Subtopic description if available",
                    "concepts": [
                      {{
                        "title": "Concept Title",
                        "description": "Concept description if available"
                      }}
                    ]
                  }}
                ]
              }}
            ]
          }}
        ]
      }}
    ]
  }}
}}

If a level is not present in the text, omit that level or use an empty array.
If you cannot determine the exact hierarchy, make your best inference based on:
- Numbering patterns (1, 1.1, 1.1.1 or I, A, 1)
- Formatting (indentation, font size, bold text - if available in context)
- Keywords (module, lesson, chapter, topic, etc.)
- Semantic coherence and logical grouping

Important guidelines:
1. Preserve the academic and pedagogical structure
2. Do not invent content that is not present in the text
3. If uncertain about a level, omit it rather than guess incorrectly
4. Focus on the intentional instructional design, not just topical headings
5. Ignore page numbers, headers, footers, and other non-content elements

Text to analyze:
{text}

Respond ONLY with the JSON structure. Do not include any additional text, explanations, or markdown formatting.
"""

    # Fallback prompt for when we need to refine results
    REFINE_STRUCTURE_PROMPT = """
You are an expert educational analyst. Review the following curriculum structure that was automatically detected
from educational text. Improve the structure by:

1. Correcting any misidentified hierarchical levels
2. Adding missing levels that are clearly present in the original text
3. Removing false positives or incorrectly grouped elements
4. Ensuring the structure follows standard educational design principles
5. Making sure titles are clear and descriptive

Current structure:
{current_structure}

Original text (for reference):
{text}

Return ONLY the improved JSON structure in the same format as before.
"""

    @classmethod
    def get_curriculum_prompt(cls, text: str) -> str:
        """
        Get the curriculum structure detection prompt.

        Args:
            text: The text to analyze.

        Returns:
            The formatted prompt.
        """
        return cls.CURRICULUM_STRUCTURE_PROMPT.format(text=text[:30000])  # Limit text length

    @classmethod
    def get_refine_prompt(cls, text: str, current_structure: Dict[str, Any]) -> str:
        """
        Get the structure refinement prompt.

        Args:
            text: The original text.
            current_structure: The currently detected structure.

        Returns:
            The formatted prompt.
        """
        import json
        return cls.REFINE_STRUCTURE_PROMPT.format(
            text=text[:10000],  # Limit text length
            current_structure=json.dumps(current_structure, indent=2)
        )