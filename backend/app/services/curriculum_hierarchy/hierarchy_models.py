"""
Pydantic schemas for Curriculum Hierarchy Service.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NodeType(str, Enum):
    UNIT = "UNIT"
    CHAPTER = "CHAPTER"
    TOPIC = "TOPIC"
    SUBTOPIC = "SUBTOPIC"
    LEARNING_OUTCOME = "LEARNING_OUTCOME"


# ── Granular Hierarchy Nodes ──────────────────────────────────────────────────

class TopicNode(BaseModel):
    id: UUID
    title: str
    sequence_number: int = 1
    description: Optional[str] = None


class ChapterNode(BaseModel):
    id: UUID
    title: str
    sequence_number: int = 1
    topics: List[TopicNode] = Field(default_factory=list)
    learning_outcomes: List[str] = Field(default_factory=list)


class UnitNode(BaseModel):
    id: UUID
    title: str
    sequence_number: int = 1
    chapters: List[ChapterNode] = Field(default_factory=list)


# ── Generic Tree Node for Raw Tree API ──────────────────────────────────────

class GenericTreeNode(BaseModel):
    id: UUID
    parent_id: Optional[UUID] = None
    node_type: NodeType
    title: str
    sequence_number: int = 1
    children: List[GenericTreeNode] = Field(default_factory=list)


# ── Curriculum Segment Model (for RAG / Transcript Mapping) ───────────────────

class CurriculumSegment(BaseModel):
    segment_id: str
    curriculum_id: UUID
    unit_id: UUID
    unit_title: str
    chapter_id: Optional[UUID] = None
    chapter_title: Optional[str] = None
    topic_ids: List[UUID] = Field(default_factory=list)
    topic_titles: List[str] = Field(default_factory=list)
    learning_outcome_ids: List[UUID] = Field(default_factory=list)
    learning_outcomes: List[str] = Field(default_factory=list)
    display_order: int = 1
    hierarchy_path: List[str] = Field(default_factory=list)


# ── Statistics Model ──────────────────────────────────────────────────────────

class CurriculumStatistics(BaseModel):
    units: int = 0
    chapters: int = 0
    topics: int = 0
    learning_outcomes: int = 0
    total_nodes: int = 0
    tree_depth: int = 0
    validation_status: str = "VALID"
    warnings: List[str] = Field(default_factory=list)


# ── Node Detail Model for Task 7 ──────────────────────────────────────────────

class NodeBrief(BaseModel):
    id: UUID
    title: str
    node_type: str
    display_order: int = 1


class NodeDetailData(BaseModel):
    node_id: UUID
    curriculum_id: UUID
    parent_id: Optional[UUID] = None
    node_type: str
    title: str
    description: Optional[str] = None
    display_order: int = 1
    sequence_number: int = 1
    hierarchy_path: List[str] = Field(default_factory=list)
    parent: Optional[NodeBrief] = None
    children: List[NodeBrief] = Field(default_factory=list)
    siblings: List[NodeBrief] = Field(default_factory=list)
    curriculum_metadata: Dict[str, Any] = Field(default_factory=dict)


class NodeDetailResponse(BaseModel):
    status: str = "success"
    message: str = "Node details retrieved successfully"
    node: NodeDetailData


# ── Response Schemas ──────────────────────────────────────────────────────────

class CurriculumHierarchyData(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    syllabus_version: str
    document_type: str
    processing_status: str
    statistics: CurriculumStatistics
    units: List[UnitNode] = Field(default_factory=list)


class CurriculumHierarchyResponse(BaseModel):
    status: str = "success"
    message: str = "Curriculum hierarchy retrieved successfully"
    curriculum: CurriculumHierarchyData


class CurriculumTreeResponse(BaseModel):
    status: str = "success"
    message: str = "Curriculum tree reconstructed successfully"
    curriculum_id: UUID
    title: str
    tree: List[GenericTreeNode] = Field(default_factory=list)


class CurriculumSegmentsResponse(BaseModel):
    status: str = "success"
    message: str = "Curriculum segments generated successfully"
    curriculum_id: UUID
    total_segments: int
    segments: List[CurriculumSegment] = Field(default_factory=list)


class CurriculumStatisticsResponse(BaseModel):
    status: str = "success"
    message: str = "Curriculum statistics retrieved successfully"
    curriculum_id: UUID
    statistics: CurriculumStatistics
