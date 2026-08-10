"""
Main Curriculum Hierarchy Service.
Integrates repository fetching, tree reconstruction, validation, segmentation, and statistics.
"""

from __future__ import annotations

import logging
from time import perf_counter
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.curriculum import Curriculum
from app.models.topic import Topic
from app.repositories.curriculum_repository import CurriculumRepository
from app.services.curriculum_hierarchy.exceptions import (
    CurriculumNotFoundError,
    EmptyCurriculumError,
)
from app.services.curriculum_hierarchy.hierarchy_models import (
    CurriculumHierarchyData,
    CurriculumHierarchyResponse,
    CurriculumSegment,
    CurriculumSegmentsResponse,
    CurriculumStatistics,
    CurriculumStatisticsResponse,
    CurriculumTreeResponse,
    GenericTreeNode,
    NodeBrief,
    NodeDetailData,
    NodeDetailResponse,
    UnitNode,
)
from app.services.curriculum_hierarchy.segment_builder import CurriculumSegmentBuilder
from app.services.curriculum_hierarchy.statistics import CurriculumStatisticsCalculator
from app.services.curriculum_hierarchy.tree_builder import CurriculumTreeBuilder
from app.services.curriculum_hierarchy.tree_validator import CurriculumTreeValidator

logger = logging.getLogger(__name__)


class CurriculumHierarchyService:
    """Service for loading and reconstructing curriculum hierarchy trees directly from PostgreSQL."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = CurriculumRepository(db)

    def _get_curriculum_and_topics(self, curriculum_id: UUID):
        start_time = perf_counter()
        logger.info("Hierarchy Loading Started for curriculum ID: %s", curriculum_id)

        curriculum = self.repository.get_curriculum_by_id(curriculum_id)
        if curriculum is None:
            logger.error("Curriculum not found: %s", curriculum_id)
            raise CurriculumNotFoundError(f"Curriculum with ID '{curriculum_id}' not found in database")

        logger.info("Curriculum Loaded: '%s' (ID: %s)", curriculum.title, curriculum.id)

        topic_rows = self.db.query(Topic).filter(Topic.curriculum_id == curriculum_id).all()
        logger.info("Topics Loaded: %d topic row(s) fetched from PostgreSQL", len(topic_rows))

        if not topic_rows:
            logger.warning("Empty Curriculum: No topics found in DB for curriculum ID: %s", curriculum_id)
            raise EmptyCurriculumError(f"Curriculum '{curriculum_id}' exists but contains no topic nodes")

        return curriculum, topic_rows, start_time

    def get_full_hierarchy(self, curriculum_id: UUID) -> CurriculumHierarchyResponse:
        curriculum, topic_rows, start_time = self._get_curriculum_and_topics(curriculum_id)

        # ── 1. Reconstruct Hierarchy ──────────────────────────────────────────
        units: list[UnitNode] = CurriculumTreeBuilder.build_structured_units(topic_rows)
        logger.info("Tree Reconstructed: %d unit(s) built", len(units))

        # ── 2. Validate Hierarchy ─────────────────────────────────────────────
        logger.info("Validation Started for curriculum ID: %s", curriculum_id)
        warnings = CurriculumTreeValidator.validate(topic_rows)
        logger.info("Validation Completed: %d warning(s) found", len(warnings))

        # ── 3. Calculate Statistics ───────────────────────────────────────────
        stats: CurriculumStatistics = CurriculumStatisticsCalculator.calculate(topic_rows, units, warnings)

        # ── 4. Build Data & Response ──────────────────────────────────────────
        hierarchy_data = CurriculumHierarchyData(
            id=curriculum.id,
            course_id=curriculum.course_id,
            title=curriculum.title,
            syllabus_version=curriculum.syllabus_version,
            document_type=curriculum.document_type,
            processing_status=curriculum.processing_status,
            statistics=stats,
            units=units,
        )

        response = CurriculumHierarchyResponse(
            status="success",
            message="Curriculum hierarchy retrieved from PostgreSQL successfully",
            curriculum=hierarchy_data,
        )

        elapsed = perf_counter() - start_time
        logger.info("API Response Generated in %.4f seconds for curriculum ID: %s", elapsed, curriculum_id)
        return response

    def get_tree_only(self, curriculum_id: UUID) -> CurriculumTreeResponse:
        curriculum, topic_rows, start_time = self._get_curriculum_and_topics(curriculum_id)

        tree: list[GenericTreeNode] = CurriculumTreeBuilder.build_generic_tree(topic_rows)
        logger.info("Tree Reconstructed: %d root node(s)", len(tree))

        response = CurriculumTreeResponse(
            status="success",
            message="Curriculum tree reconstructed from PostgreSQL successfully",
            curriculum_id=curriculum.id,
            title=curriculum.title,
            tree=tree,
        )

        elapsed = perf_counter() - start_time
        logger.info("API Response Generated in %.4f seconds for tree endpoint", elapsed)
        return response

    def get_segments(self, curriculum_id: UUID) -> CurriculumSegmentsResponse:
        curriculum, topic_rows, start_time = self._get_curriculum_and_topics(curriculum_id)

        topic_map = {t.id: t for t in topic_rows}
        units: list[UnitNode] = CurriculumTreeBuilder.build_structured_units(topic_rows)
        segments: list[CurriculumSegment] = CurriculumSegmentBuilder.build_segments(curriculum.id, units, topic_map)
        logger.info("Segments Generated: %d logical segment(s) built", len(segments))

        response = CurriculumSegmentsResponse(
            status="success",
            message="Curriculum segments generated successfully for AI pipelines",
            curriculum_id=curriculum.id,
            total_segments=len(segments),
            segments=segments,
        )

        elapsed = perf_counter() - start_time
        logger.info("API Response Generated in %.4f seconds for segments endpoint", elapsed)
        return response

    def get_statistics(self, curriculum_id: UUID) -> CurriculumStatisticsResponse:
        curriculum, topic_rows, start_time = self._get_curriculum_and_topics(curriculum_id)

        units: list[UnitNode] = CurriculumTreeBuilder.build_structured_units(topic_rows)
        warnings = CurriculumTreeValidator.validate(topic_rows)
        stats: CurriculumStatistics = CurriculumStatisticsCalculator.calculate(topic_rows, units, warnings)

        response = CurriculumStatisticsResponse(
            status="success",
            message="Curriculum statistics calculated successfully",
            curriculum_id=curriculum.id,
            statistics=stats,
        )

        elapsed = perf_counter() - start_time
        logger.info("API Response Generated in %.4f seconds for statistics endpoint", elapsed)
        return response

    def get_node_detail(self, curriculum_id: UUID, node_id: UUID) -> NodeDetailResponse:
        """Task 7: Returns complete information for a specific node in O(n) in-memory complexity."""
        curriculum, topic_rows, start_time = self._get_curriculum_and_topics(curriculum_id)

        topic_map: dict[UUID, Topic] = {t.id: t for t in topic_rows}
        target_node = topic_map.get(node_id)
        if target_node is None:
            raise CurriculumNotFoundError(f"Node '{node_id}' not found under curriculum '{curriculum_id}'")

        path = CurriculumTreeBuilder.get_hierarchy_path(node_id, topic_map)

        parent_brief = None
        if target_node.parent_topic_id and target_node.parent_topic_id in topic_map:
            p = topic_map[target_node.parent_topic_id]
            parent_brief = NodeBrief(
                id=p.id,
                title=p.topic_name,
                node_type=p.node_type or "CHAPTER",
                display_order=p.display_order or p.sequence_number or 1,
            )

        children_briefs = []
        for t in sorted(topic_rows, key=lambda x: x.sequence_number):
            if t.parent_topic_id == node_id:
                children_briefs.append(
                    NodeBrief(
                        id=t.id,
                        title=t.topic_name,
                        node_type=t.node_type or "TOPIC",
                        display_order=t.display_order or t.sequence_number or 1,
                    )
                )

        sibling_briefs = []
        for t in sorted(topic_rows, key=lambda x: x.sequence_number):
            if t.parent_topic_id == target_node.parent_topic_id and t.id != node_id:
                sibling_briefs.append(
                    NodeBrief(
                        id=t.id,
                        title=t.topic_name,
                        node_type=t.node_type or "TOPIC",
                        display_order=t.display_order or t.sequence_number or 1,
                    )
                )

        node_data = NodeDetailData(
            node_id=target_node.id,
            curriculum_id=curriculum.id,
            parent_id=target_node.parent_topic_id,
            node_type=target_node.node_type or ("UNIT" if target_node.parent_topic_id is None else "TOPIC"),
            title=target_node.topic_name,
            description=None,
            display_order=target_node.display_order or target_node.sequence_number or 1,
            sequence_number=target_node.sequence_number or 1,
            hierarchy_path=path,
            parent=parent_brief,
            children=children_briefs,
            siblings=sibling_briefs,
            curriculum_metadata={
                "title": curriculum.title,
                "course_id": curriculum.course_id,
                "syllabus_version": curriculum.syllabus_version,
            },
        )

        response = NodeDetailResponse(
            status="success",
            message="Node details retrieved successfully",
            node=node_data,
        )

        elapsed = perf_counter() - start_time
        logger.info("API Response Generated in %.4f seconds for node detail endpoint", elapsed)
        return response
