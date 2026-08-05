"""
Classroom Interaction Engine — Evaluates student-faculty engagement and density.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class InteractionEngine:
    FACULTY_QUESTION_PATTERNS = [
        r"\bany questions\b",
        r"\bdoes anyone know\b",
        r"\bcan anyone tell\b",
        r"\bwhat do you think\b",
        r"\bwhy is that\b",
        r"\bwho can answer\b",
        r"\bhow would you solve\b",
        r"\bdo you agree\b",
    ]

    RECAP_PATTERNS = [
        r"\bwhat did we cover\b",
        r"\bremember from last class\b",
        r"\bwho remembers\b",
    ]

    CLARIFICATION_PATTERNS = [
        r"\bis that clear\b",
        r"\bmake sense\b",
        r"\bany doubts\b",
        r"\bwith me so far\b",
    ]

    def analyze(self, transcript_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not transcript_chunks:
            return {
                "score": 0.0,
                "faculty_question_count": 0,
                "student_question_count": 0,
                "faculty_answer_count": 0,
                "student_response_count": 0,
                "interaction_density": 0.0,
                "engagement_opportunities": 0,
                "clarification_requests": 0,
                "recap_questions": 0,
            }

        faculty_questions = 0
        student_questions = 0
        student_responses = 0
        faculty_answers = 0
        recap_questions = 0
        clarification_requests = 0

        for chunk in transcript_chunks:
            speaker = str(chunk.get("speaker", "Faculty")).strip()
            text = chunk.get("text", "")

            is_student = "student" in speaker.lower()
            is_question = "?" in text

            if is_student:
                if is_question:
                    student_questions += 1
                else:
                    student_responses += 1
            else:
                if is_question:
                    # Check if recap or clarification or general faculty question
                    if any(re.search(p, text, re.IGNORECASE) for p in self.RECAP_PATTERNS):
                        recap_questions += 1
                    elif any(re.search(p, text, re.IGNORECASE) for p in self.CLARIFICATION_PATTERNS):
                        clarification_requests += 1

                    if any(re.search(p, text, re.IGNORECASE) for p in self.FACULTY_QUESTION_PATTERNS) or is_question:
                        faculty_questions += 1

                # If student previously asked a question, faculty response counts as answer
                if student_questions > faculty_answers:
                    faculty_answers += 1

        total_interactions = (
            faculty_questions + student_questions + student_responses + clarification_requests
        )
        total_chunks = max(1, len(transcript_chunks))
        interaction_density = round(total_interactions / total_chunks, 2)
        engagement_opportunities = faculty_questions + clarification_requests + recap_questions

        # Calculate interaction score (0-100)
        # Score factors: interaction density, student responses, engagement opportunities
        base_score = min(50.0, engagement_opportunities * 10.0)
        student_bonus = min(30.0, (student_responses + student_questions) * 15.0)
        density_bonus = min(20.0, interaction_density * 40.0)

        score = round(base_score + student_bonus + density_bonus, 1)

        return {
            "score": score,
            "faculty_question_count": faculty_questions,
            "student_question_count": student_questions,
            "faculty_answer_count": faculty_answers,
            "student_response_count": student_responses,
            "interaction_density": interaction_density,
            "engagement_opportunities": engagement_opportunities,
            "clarification_requests": clarification_requests,
            "recap_questions": recap_questions,
        }
