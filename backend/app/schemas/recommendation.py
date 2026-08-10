"""
Pydantic Schemas for the Recommendation Engine API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Input Schemas ─────────────────────────────────────────────────────────────

class RecommendationGenerateRequest(BaseModel):
    lecture_id: UUID
    curriculum_id: Optional[UUID] = None
    faculty_id: Optional[UUID] = None
    force_reanalyze: bool = False


# ── Response Schemas ──────────────────────────────────────────────────────────

class SupportingEvidenceItem(BaseModel):
    source: str                           # "coverage" | "validation" | "teaching"
    evidence_type: str                    # e.g. "SKIPPED_TOPIC", "FORMULA_ERROR"
    description: str
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    topic_name: Optional[str] = None


class RecommendationItemResponse(BaseModel):
    id: str
    category: str                         # "Coverage" | "Validation" | "Pedagogical"
    priority: str                         # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFORMATIONAL"
    priority_score: float = 0.0
    title: str
    reason: str
    recommended_action: str
    confidence: float = 90.0
    supporting_evidence: List[SupportingEvidenceItem] = Field(default_factory=list)
    raw_reason: Optional[str] = None
    merged_from: Optional[List[str]] = None


class RecommendationGenerateData(BaseModel):
    lecture_id: str
    total_recommendations: int
    critical: int
    high: int
    medium: int
    low: int
    informational: int = 0
    analysis_reused: bool = False
    recommendations: List[RecommendationItemResponse] = Field(default_factory=list)


class PriorityBreakdownResponse(BaseModel):
    id: str
    title: str
    category: str
    priority_level: str
    priority_score: float
    severity: float
    impact: float
    urgency: float
    frequency: float
    confidence: float


class WeeklySummaryResponse(BaseModel):
    faculty_id: str
    week_label: str
    lecture_count: int
    total_recommendations: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    repeated_weaknesses: List[str] = Field(default_factory=list)
    improving_areas: List[str] = Field(default_factory=list)
    declining_areas: List[str] = Field(default_factory=list)
    frequently_skipped_topics: List[str] = Field(default_factory=list)
    frequently_incorrect_concepts: List[str] = Field(default_factory=list)
    avg_coverage_score: float = 0.0
    avg_validation_score: float = 0.0
    avg_teaching_score: float = 0.0
    summary_text: Optional[str] = None


class MonthlySummaryResponse(BaseModel):
    faculty_id: str
    month_label: str
    week_count: int
    lecture_count: int
    total_recommendations: int
    coverage_trend: List[float] = Field(default_factory=list)
    validation_trend: List[float] = Field(default_factory=list)
    teaching_trend: List[float] = Field(default_factory=list)
    interaction_trend: List[float] = Field(default_factory=list)
    overall_progress_score: float = 0.0
    monthly_improvement_report: Optional[str] = None
    top_recurring_issues: List[str] = Field(default_factory=list)
    most_improved_areas: List[str] = Field(default_factory=list)


class RecommendationHistoryItem(BaseModel):
    analysis_id: str
    lecture_id: str
    created_at: str
    total_recommendations: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    top_priority_category: Optional[str] = None
    is_active: bool = True
