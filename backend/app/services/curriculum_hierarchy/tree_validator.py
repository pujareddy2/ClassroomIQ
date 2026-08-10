"""
Validation service for curriculum tree hierarchy integrity.
Performs non-crashing structural validation — returns warnings and status.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Set
from uuid import UUID

from app.models.topic import Topic
from app.services.curriculum_hierarchy.exceptions import EmptyCurriculumError

logger = logging.getLogger(__name__)


class CurriculumTreeValidator:
    """Validates structural integrity of topic nodes for a curriculum."""

    @staticmethod
    def validate(topic_rows: List[Topic]) -> List[str]:
        """
        Validates topic hierarchy and returns a list of warning messages.
        Does not crash on non-fatal anomalies.
        """
        warnings: List[str] = []

        if not topic_rows:
            raise EmptyCurriculumError("No topic nodes found for this curriculum")

        topic_map: Dict[UUID, Topic] = {t.id: t for t in topic_rows}
        all_ids: Set[UUID] = set(topic_map.keys())

        # ── 1. Check Orphan Nodes & Invalid Parent IDs ─────────────────────────
        for topic in topic_rows:
            if topic.parent_topic_id is not None and topic.parent_topic_id not in all_ids:
                warnings.append(
                    f"Orphan Node: Topic '{topic.topic_name}' ({topic.id}) references "
                    f"invalid parent_topic_id '{topic.parent_topic_id}'"
                )

        # ── 2. Check Circular References ──────────────────────────────────────
        for topic in topic_rows:
            visited: Set[UUID] = set()
            curr: Topic | None = topic
            while curr is not None and curr.parent_topic_id is not None:
                if curr.id in visited:
                    msg = f"Circular Reference detected involving topic '{curr.topic_name}' ({curr.id})"
                    warnings.append(msg)
                    logger.error(msg)
                    break
                visited.add(curr.id)
                curr = topic_map.get(curr.parent_topic_id)

        # ── 3. Check Duplicate Node Names under Same Parent ────────────────────
        parent_children_names: Dict[UUID | None, List[str]] = {}
        for topic in topic_rows:
            parent_children_names.setdefault(topic.parent_topic_id, []).append(topic.topic_name.strip().lower())

        for parent_id, names in parent_children_names.items():
            seen: Set[str] = set()
            for name in names:
                if name in seen:
                    warnings.append(f"Duplicate node name '{name}' under parent ID '{parent_id}'")
                seen.add(name)

        # ── 4. Check Display Order & Sequence Number Gaps ────────────────────
        parent_children: Dict[UUID | None, List[Topic]] = {}
        for topic in topic_rows:
            parent_children.setdefault(topic.parent_topic_id, []).append(topic)

        for parent_id, children in parent_children.items():
            disp_orders = [c.display_order for c in children if c.display_order is not None]
            if len(disp_orders) > 1 and len(disp_orders) != len(set(disp_orders)):
                warnings.append(f"Duplicate display_order numbers found under parent ID '{parent_id}'")

        # ── 5. Check Root Nodes & Disconnected Subtrees ──────────────────────
        root_nodes = parent_children.get(None, [])
        if not root_nodes:
            warnings.append("Missing Root Nodes: No top-level Unit nodes (parent_topic_id = NULL) found")

        # Check for disconnected components (nodes unreachable from any root)
        reachable: Set[UUID] = set()

        def _traverse(node_id: UUID):
            reachable.add(node_id)
            for child in parent_children.get(node_id, []):
                if child.id not in reachable:
                    _traverse(child.id)

        for root in root_nodes:
            _traverse(root.id)

        unreachable = all_ids - reachable
        if unreachable:
            warnings.append(f"Disconnected Tree: {len(unreachable)} node(s) are unreachable from root nodes")

        logger.info("Hierarchy validation completed with %d warning(s)", len(warnings))
        return warnings
