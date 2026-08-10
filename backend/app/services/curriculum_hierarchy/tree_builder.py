"""
Tree builder for reconstructing data-driven curriculum hierarchy from PostgreSQL Topic records.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.models.topic import Topic
from app.services.curriculum_hierarchy.hierarchy_models import (
    ChapterNode,
    GenericTreeNode,
    NodeType,
    TopicNode,
    UnitNode,
)

logger = logging.getLogger(__name__)


def sort_topic_rows(rows: List[Topic]) -> List[Topic]:
    """
    Deterministic sort:
    1. display_order
    2. sequence_number
    3. created_at timestamp
    4. string ID
    """
    def key_fn(t: Topic):
        disp = t.display_order if t.display_order is not None else float("inf")
        seq = t.sequence_number if t.sequence_number is not None else float("inf")
        created = t.created_at.timestamp() if getattr(t, "created_at", None) else 0.0
        return (disp, seq, created, str(t.id))

    return sorted(rows, key=key_fn)


class CurriculumTreeBuilder:
    """Reconstructs data-driven tree nodes and builds in-memory hierarchy paths."""

    @staticmethod
    def get_hierarchy_path(node_id: UUID, topic_map: Dict[UUID, Topic]) -> List[str]:
        """
        Dynamically generates root-to-node path in memory.
        Example: ["Unit 1", "Lexical Analysis", "Finite Automata"]
        """
        path: List[str] = []
        curr: Topic | None = topic_map.get(node_id)
        visited = set()

        while curr is not None:
            if curr.id in visited:
                break
            visited.add(curr.id)
            # Exclude metadata wrapper nodes like "Learning Outcomes" if desired, or include all
            path.append(curr.topic_name)
            if curr.parent_topic_id is None:
                break
            curr = topic_map.get(curr.parent_topic_id)

        path.reverse()
        return path

    @staticmethod
    def build_structured_units(topic_rows: List[Topic]) -> List[UnitNode]:
        """
        Data-driven reconstruction of UnitNode -> ChapterNode -> TopicNode hierarchy.
        Supports Units without Chapters, Units directly containing Topics, etc.
        """
        if not topic_rows:
            return []

        sorted_rows = sort_topic_rows(topic_rows)
        children_map: Dict[Optional[UUID], List[Topic]] = {}
        for t in sorted_rows:
            children_map.setdefault(t.parent_topic_id, []).append(t)

        unit_nodes: List[UnitNode] = []
        root_topics = children_map.get(None, [])

        unit_seq = 1
        for u_topic in root_topics:
            chapters: List[ChapterNode] = []
            direct_topics: List[TopicNode] = []
            direct_outcomes: List[str] = []

            child_rows = children_map.get(u_topic.id, [])
            chap_seq = 1

            for c_topic in child_rows:
                raw_type = (c_topic.node_type or "").upper().strip()

                # Case: Direct Topic under Unit (Case B)
                if raw_type in ("TOPIC", "SUBTOPIC"):
                    direct_topics.append(
                        TopicNode(
                            id=c_topic.id,
                            title=c_topic.topic_name,
                            sequence_number=c_topic.sequence_number,
                        )
                    )
                    continue

                # Case: Direct Learning Outcome under Unit (Case D)
                if raw_type == "LEARNING_OUTCOME":
                    direct_outcomes.append(c_topic.topic_name)
                    continue

                # Case: Chapter / Section under Unit (Case A, Case C)
                leaf_topics: List[TopicNode] = []
                learning_outcomes: List[str] = []
                leaf_rows = children_map.get(c_topic.id, [])
                top_seq = 1

                for leaf in leaf_rows:
                    leaf_type = (leaf.node_type or "").upper().strip()
                    if leaf_type == "LEARNING_OUTCOME" or c_topic.topic_name == "Learning Outcomes":
                        learning_outcomes.append(leaf.topic_name)
                    else:
                        leaf_topics.append(
                            TopicNode(
                                id=leaf.id,
                                title=leaf.topic_name,
                                sequence_number=top_seq,
                            )
                        )
                        top_seq += 1

                if c_topic.topic_name != "Learning Outcomes":
                    chapters.append(
                        ChapterNode(
                            id=c_topic.id,
                            title=c_topic.topic_name,
                            sequence_number=chap_seq,
                            topics=leaf_topics,
                            learning_outcomes=learning_outcomes,
                        )
                    )
                    chap_seq += 1
                else:
                    if chapters:
                        chapters[-1].learning_outcomes.extend(learning_outcomes)

            # If Unit has direct topics/outcomes without chapters, wrap them in a default chapter
            if direct_topics or direct_outcomes:
                chapters.append(
                    ChapterNode(
                        id=u_topic.id,
                        title=f"{u_topic.topic_name} - General Topics",
                        sequence_number=chap_seq,
                        topics=direct_topics,
                        learning_outcomes=direct_outcomes,
                    )
                )

            unit_nodes.append(
                UnitNode(
                    id=u_topic.id,
                    title=u_topic.topic_name,
                    sequence_number=unit_seq,
                    chapters=chapters,
                )
            )
            unit_seq += 1

        return unit_nodes

    @staticmethod
    def build_generic_tree(topic_rows: List[Topic]) -> List[GenericTreeNode]:
        """
        Builds raw tree using parent_topic_id with deterministic sorting.
        """
        if not topic_rows:
            return []

        sorted_rows = sort_topic_rows(topic_rows)
        children_map: Dict[Optional[UUID], List[Topic]] = {}
        for t in sorted_rows:
            children_map.setdefault(t.parent_topic_id, []).append(t)

        def _build_node(topic: Topic) -> GenericTreeNode:
            if topic.node_type:
                try:
                    n_type = NodeType(topic.node_type)
                except ValueError:
                    n_type = NodeType.TOPIC
            elif topic.parent_topic_id is None:
                n_type = NodeType.UNIT
            elif topic.topic_name == "Learning Outcomes":
                n_type = NodeType.LEARNING_OUTCOME
            else:
                n_type = NodeType.CHAPTER

            child_rows = children_map.get(topic.id, [])
            child_nodes = [_build_node(c) for c in child_rows]

            return GenericTreeNode(
                id=topic.id,
                parent_id=topic.parent_topic_id,
                node_type=n_type,
                title=topic.topic_name,
                sequence_number=topic.sequence_number,
                children=child_nodes,
            )

        root_rows = children_map.get(None, [])
        return [_build_node(r) for r in root_rows]
