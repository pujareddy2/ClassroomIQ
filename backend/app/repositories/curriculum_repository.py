"""
CurriculumRepository — all DB operations for curriculum domain.

Extends BaseRepository for shared course/faculty/term helpers.
Adds list_curricula() and soft_delete_curriculum() for new API endpoints.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.curriculum import Curriculum
from app.models.topic import Topic
from app.repositories.base_repository import BaseRepository
from app.schemas.curriculum import ChapterSchema, ParsedCurriculumSchema, UnitSchema
from app.schemas.pagination import PaginationMeta, make_pagination_meta


class CurriculumRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    # ── Single Record Lookups ─────────────────────────────────────────────────

    def get_curriculum_by_id(self, curriculum_id: UUID) -> Curriculum | None:
        return self.db.get(Curriculum, curriculum_id)

    # ── List & Pagination ─────────────────────────────────────────────────────

    def list_curricula(
        self,
        page: int = 1,
        page_size: int = 20,
        course_id: UUID | None = None,
        faculty_id: UUID | None = None,
        status: str = "ACTIVE",
    ) -> tuple[list[Curriculum], PaginationMeta]:
        """Return a paginated list of curricula with optional filters."""
        stmt = select(Curriculum).where(Curriculum.status == status)

        if course_id is not None:
            stmt = stmt.where(Curriculum.course_id == course_id)
        if faculty_id is not None:
            stmt = stmt.where(Curriculum.faculty_id == faculty_id)

        # Count total before paginating
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_items = int(self.db.execute(count_stmt).scalar_one())

        # Apply ordering + pagination
        stmt = stmt.order_by(Curriculum.uploaded_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.execute(stmt).scalars().all())

        return items, make_pagination_meta(page, page_size, total_items)

    def list_curricula_by_owner(
        self,
        owner_id: UUID,
        page: int = 1,
        page_size: int = 20,
        course_id: UUID | None = None,
        status: str = "ACTIVE",
    ) -> tuple[list[Curriculum], PaginationMeta]:
        """Return curricula belonging to the authenticated user (created_by = owner_id).

        This is the TENANT-SAFE query — a faculty member only sees their own courses.
        """
        stmt = select(Curriculum).where(
            Curriculum.status == status,
            Curriculum.created_by == owner_id,
        )

        if course_id is not None:
            stmt = stmt.where(Curriculum.course_id == course_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_items = int(self.db.execute(count_stmt).scalar_one())

        stmt = stmt.order_by(Curriculum.uploaded_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.execute(stmt).scalars().all())

        return items, make_pagination_meta(page, page_size, total_items)

    # ── Soft Delete ───────────────────────────────────────────────────────────

    def soft_delete_curriculum(self, curriculum_id: UUID) -> Curriculum | None:
        """Set status=DELETED and deleted_at=now() — does NOT physically remove the row."""
        curriculum = self.get_curriculum_by_id(curriculum_id)
        if curriculum is None:
            return None
        curriculum.status = "DELETED"
        curriculum.deleted_at = datetime.now(timezone.utc)
        self.db.flush()
        return curriculum

    # ── Count ─────────────────────────────────────────────────────────────────

    def count_curricula_for_course_term(self, course_id: UUID, academic_term_id: UUID) -> int:
        stmt = select(func.count(Curriculum.id)).where(
            Curriculum.course_id == course_id,
            Curriculum.academic_term_id == academic_term_id,
        )
        return int(self.db.execute(stmt).scalar_one())

    # ── Write ─────────────────────────────────────────────────────────────────

    def create_curriculum(self, curriculum: Curriculum) -> Curriculum:
        self.db.add(curriculum)
        self.db.flush()
        self.db.refresh(curriculum)
        return curriculum

    def delete_topics_for_curriculum(self, curriculum_id: UUID) -> None:
        """Remove existing topics for a curriculum to prevent duplicate storage."""
        stmt = select(Topic).where(Topic.curriculum_id == curriculum_id)
        existing = self.db.execute(stmt).scalars().all()
        for t in existing:
            self.db.delete(t)
        self.db.flush()

    def save_topics_from_parsed_curriculum(
        self, curriculum_id: UUID, parsed: ParsedCurriculumSchema
    ) -> list[Topic]:
        """Persist parsed Units, Chapters, and Topics as hierarchical Topic rows."""
        self.delete_topics_for_curriculum(curriculum_id)
        created_topics: list[Topic] = []

        unit_seq = 1
        for unit in parsed.units:
            unit_title_text = (
                f"Unit {unit.unit_number}: {unit.title}"
                if not unit.title.lower().startswith("unit")
                else unit.title
            )
            unit_topic = Topic(
                curriculum_id=curriculum_id,
                parent_topic_id=None,
                topic_name=unit_title_text,
                node_type="UNIT",
                display_order=unit_seq,
                expected_hours=1,
                sequence_number=unit_seq,
            )
            self.db.add(unit_topic)
            self.db.flush()
            self.db.refresh(unit_topic)
            created_topics.append(unit_topic)
            unit_seq += 1

            chap_seq = 1
            for chap in unit.chapters:
                chap_topic = Topic(
                    curriculum_id=curriculum_id,
                    parent_topic_id=unit_topic.id,
                    topic_name=chap.title,
                    node_type="CHAPTER",
                    display_order=chap_seq,
                    expected_hours=1,
                    sequence_number=chap_seq,
                )
                self.db.add(chap_topic)
                self.db.flush()
                self.db.refresh(chap_topic)
                created_topics.append(chap_topic)
                chap_seq += 1

                topic_seq = 1
                for top_str in chap.topics:
                    leaf_topic = Topic(
                        curriculum_id=curriculum_id,
                        parent_topic_id=chap_topic.id,
                        topic_name=top_str,
                        node_type="TOPIC",
                        display_order=topic_seq,
                        expected_hours=1,
                        sequence_number=topic_seq,
                    )
                    self.db.add(leaf_topic)
                    self.db.flush()
                    self.db.refresh(leaf_topic)
                    created_topics.append(leaf_topic)
                    topic_seq += 1

            if unit.learning_outcomes:
                lo_chap_topic = Topic(
                    curriculum_id=curriculum_id,
                    parent_topic_id=unit_topic.id,
                    topic_name="Learning Outcomes",
                    node_type="CHAPTER",
                    display_order=chap_seq,
                    expected_hours=1,
                    sequence_number=chap_seq,
                )
                self.db.add(lo_chap_topic)
                self.db.flush()
                self.db.refresh(lo_chap_topic)
                created_topics.append(lo_chap_topic)
                chap_seq += 1

                lo_seq = 1
                for lo_str in unit.learning_outcomes:
                    lo_leaf = Topic(
                        curriculum_id=curriculum_id,
                        parent_topic_id=lo_chap_topic.id,
                        topic_name=lo_str,
                        node_type="LEARNING_OUTCOME",
                        display_order=lo_seq,
                        expected_hours=1,
                        sequence_number=lo_seq,
                    )
                    self.db.add(lo_leaf)
                    self.db.flush()
                    self.db.refresh(lo_leaf)
                    created_topics.append(lo_leaf)
                    lo_seq += 1

        return created_topics

    def load_parsed_curriculum_from_db(self, curriculum: Curriculum) -> ParsedCurriculumSchema:
        """Reconstruct ParsedCurriculumSchema directly from database Topic records."""
        stmt = select(Topic).where(Topic.curriculum_id == curriculum.id).order_by(Topic.sequence_number)
        all_topics = self.db.execute(stmt).scalars().all()

        if not all_topics:
            return ParsedCurriculumSchema(title=curriculum.title, course_id=curriculum.course_id, units=[])

        children_map: dict[UUID | None, list[Topic]] = {}
        for t in all_topics:
            children_map.setdefault(t.parent_topic_id, []).append(t)

        units: list[UnitSchema] = []
        unit_nodes = children_map.get(None, [])

        unit_idx = 1
        for u_node in unit_nodes:
            chapters: list[ChapterSchema] = []
            learning_outcomes: list[str] = []
            chap_nodes = children_map.get(u_node.id, [])
            for c_node in chap_nodes:
                leaf_nodes = children_map.get(c_node.id, [])
                leaf_topic_names = [leaf.topic_name for leaf in leaf_nodes]
                if c_node.topic_name == "Learning Outcomes":
                    learning_outcomes = leaf_topic_names
                else:
                    chapters.append(ChapterSchema(title=c_node.topic_name, topics=leaf_topic_names))

            units.append(
                UnitSchema(
                    unit_number=unit_idx,
                    title=u_node.topic_name,
                    chapters=chapters,
                    learning_outcomes=learning_outcomes,
                )
            )
            unit_idx += 1

        return ParsedCurriculumSchema(title=curriculum.title, course_id=curriculum.course_id, units=units)
