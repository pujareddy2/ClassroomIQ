"""
Reference Retriever component for Technical Validation Engine.
Retrieves official syllabus, reference books, lecture notes, and extracted curriculum text
for a specific topic or curriculum.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.curriculum import Curriculum
from app.models.reference_material import ReferenceMaterial
from app.models.topic_reference import TopicReference
from app.models.topic import Topic

logger = logging.getLogger(__name__)


class ReferenceRetriever:
    """Retrieves academic reference materials for a given topic/curriculum."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def retrieve_references_for_topic(
        self,
        curriculum_id: UUID,
        topic_id: Optional[UUID] = None,
        topic_name: Optional[str] = None,
    ) -> List[Tuple[Optional[UUID], str, str, str]]:
        """
        Returns a list of reference tuples:
            [(reference_material_id, document_title, section_name, excerpt_text), ...]
        """
        results: List[Tuple[Optional[UUID], str, str, str]] = []

        # 1. Fetch from topic_references table if topic_id is provided
        if topic_id:
            stmt = (
                select(ReferenceMaterial)
                .join(TopicReference, TopicReference.reference_material_id == ReferenceMaterial.id)
                .where(TopicReference.topic_id == topic_id)
            )
            refs = self.db.execute(stmt).scalars().all()
            for ref in refs:
                results.append((
                    ref.id,
                    ref.title,
                    f"Section: {topic_name or 'Topic'}",
                    ref.description or f"Reference document for {topic_name or 'Topic'}",
                ))

        # 2. Fetch course-level reference materials if curriculum course is linked
        curriculum = self.db.get(Curriculum, curriculum_id)
        if curriculum and curriculum.course_id:
            stmt2 = select(ReferenceMaterial).where(ReferenceMaterial.course_id == curriculum.course_id)
            course_refs = self.db.execute(stmt2).scalars().all()
            for ref in course_refs:
                if not any(r[0] == ref.id for r in results):
                    results.append((
                        ref.id,
                        ref.title,
                        ref.document_type or "Reference Book",
                        ref.description or f"Academic reference for course {curriculum.title}",
                    ))

        # 3. Always include Curriculum Syllabus extracted_text as primary reference
        if curriculum and curriculum.extracted_text:
            text_excerpt = curriculum.extracted_text
            if topic_name:
                # Extract relevant snippet around topic_name if possible
                pos = text_excerpt.lower().find(topic_name.lower())
                if pos != -1:
                    start_pos = max(0, pos - 100)
                    end_pos = min(len(text_excerpt), pos + 400)
                    text_excerpt = text_excerpt[start_pos:end_pos]
                elif len(text_excerpt) > 500:
                    text_excerpt = text_excerpt[:500]

            results.append((
                None,
                f"Official Syllabus ({curriculum.title})",
                f"Syllabus Content: {topic_name or 'General'}",
                text_excerpt,
            ))

        # Default fallback reference if nothing extracted yet
        if not results:
            results.append((
                None,
                "Curriculum Knowledge Base",
                f"Topic Syllabus: {topic_name or 'General'}",
                f"Standard Academic Definition and concepts for {topic_name or 'Curriculum Topic'}.",
            ))

        return results
