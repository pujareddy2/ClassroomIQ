"""
EvidenceCollectorService

Collects outputs from all four upstream AI engines:
  - Coverage Engine   → CoverageResult rows with status != COVERED
  - Validation Engine → ValidationResult rows with status in (INCORRECT, FORMULA_ERROR, CODE_ERROR)
  - Teaching Engine   → TeachingAnalysis + TeachingSummary with low sub-scores
  - Recommendation    → RecItem rows with priority CRITICAL or HIGH

Returns a structured list of EvidenceCandidate dataclasses — raw facts that
the ExplanationBuilderService will transform into ExplanationRecord + EvidenceItem rows.

Rules:
  - Never reload transcript or curriculum data — reference by FK only.
  - Batch load evidence with single queries per engine.
  - Target O(n) query complexity.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.coverage_result import CoverageResult
from app.models.coverage_summary import CoverageSummary
from app.models.recommendation_engine import RecAnalysis, RecItem
from app.models.teaching_intelligence import TeachingAnalysis, TeachingSummary
from app.models.validation_result import ValidationResult
from app.models.validation_summary import ValidationSummary

logger = logging.getLogger(__name__)


@dataclass
class EvidenceCandidate:
    """A single upstream AI decision that needs an explanation."""
    source: str             # 'coverage' | 'validation' | 'teaching' | 'recommendation'
    decision_type: str      # e.g. 'SKIPPED_TOPIC', 'INCORRECT_CONCEPT', 'WEAK_EXPLANATION'
    decision_id: UUID       # PK of the upstream record
    subject: str            # Human-readable subject label
    description: str        # Full description of the issue
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None


@dataclass
class CollectedEvidence:
    """Bundle of all evidence candidates for a single lecture."""
    lecture_id: UUID
    candidates: List[EvidenceCandidate] = field(default_factory=list)

    # Upstream summary IDs for traceability
    coverage_summary_id: Optional[UUID] = None
    validation_summary_id: Optional[UUID] = None
    teaching_analysis_id: Optional[UUID] = None
    rec_analysis_id: Optional[UUID] = None


class EvidenceCollectorService:
    """
    Aggregates raw facts from all 4 upstream engines into EvidenceCandidate objects.
    Does NOT persist anything — that's the ExplanationBuilderService's responsibility.
    """

    def __init__(self, db: Session):
        self.db = db

    def collect(self, lecture_id: UUID) -> CollectedEvidence:
        """Single entry point — collects from all 4 engines."""
        logger.info("Evidence Collection Started — lecture_id=%s", lecture_id)

        bundle = CollectedEvidence(lecture_id=lecture_id)

        self._collect_coverage(lecture_id, bundle)
        self._collect_validation(lecture_id, bundle)
        self._collect_teaching(lecture_id, bundle)
        self._collect_recommendations(lecture_id, bundle)

        logger.info(
            "Evidence Collection Complete — lecture_id=%s, total_candidates=%d",
            lecture_id, len(bundle.candidates),
        )
        return bundle

    # ── Coverage ─────────────────────────────────────────────────────────────

    def _collect_coverage(self, lecture_id: UUID, bundle: CollectedEvidence) -> None:
        cov_summary = (
            self.db.query(CoverageSummary)
            .filter(CoverageSummary.lecture_id == lecture_id, CoverageSummary.status == "ACTIVE")
            .first()
        )
        if not cov_summary:
            return
        bundle.coverage_summary_id = cov_summary.id

        flagged_statuses = ("SKIPPED", "PARTIALLY_COVERED", "RUSHED")
        results = (
            self.db.query(CoverageResult)
            .filter(
                CoverageResult.lecture_id == lecture_id,
                CoverageResult.status == "ACTIVE",
                CoverageResult.coverage_status.in_(flagged_statuses),
            )
            .all()
        )
        for cr in results:
            bundle.candidates.append(
                EvidenceCandidate(
                    source="coverage",
                    decision_type=f"COVERAGE_{cr.coverage_status}",
                    decision_id=cr.id,
                    subject=cr.topic_name,
                    description=(
                        f"Topic '{cr.topic_name}' is {cr.coverage_status} "
                        f"({cr.coverage_percentage:.1f}% covered)"
                    ),
                    metric_name="coverage_percentage",
                    metric_value=cr.coverage_percentage,
                )
            )

    # ── Validation ───────────────────────────────────────────────────────────

    def _collect_validation(self, lecture_id: UUID, bundle: CollectedEvidence) -> None:
        val_summary = (
            self.db.query(ValidationSummary)
            .filter(ValidationSummary.lecture_id == lecture_id, ValidationSummary.status == "ACTIVE")
            .first()
        )
        if not val_summary:
            return
        bundle.validation_summary_id = val_summary.id

        flagged_statuses = ("INCORRECT", "FORMULA_ERROR", "CODE_ERROR")
        results = (
            self.db.query(ValidationResult)
            .filter(
                ValidationResult.lecture_id == lecture_id,
                ValidationResult.status == "ACTIVE",
                ValidationResult.validation_status.in_(flagged_statuses),
            )
            .all()
        )
        for vr in results:
            bundle.candidates.append(
                EvidenceCandidate(
                    source="validation",
                    decision_type=f"VALIDATION_{vr.validation_status}",
                    decision_id=vr.id,
                    subject=f"Validation flag in chunk [{vr.chunk_id}]",
                    description=vr.reason,
                    metric_name="confidence_score",
                    metric_value=vr.confidence_score,
                )
            )

    # ── Teaching Intelligence ────────────────────────────────────────────────

    def _collect_teaching(self, lecture_id: UUID, bundle: CollectedEvidence) -> None:
        tch_analysis = (
            self.db.query(TeachingAnalysis)
            .filter(TeachingAnalysis.lecture_id == lecture_id, TeachingAnalysis.is_active == True)
            .first()
        )
        if not tch_analysis:
            return
        bundle.teaching_analysis_id = tch_analysis.id

        tch_summary = (
            self.db.query(TeachingSummary)
            .filter(TeachingSummary.analysis_id == tch_analysis.id)
            .first()
        )
        if not tch_summary:
            return

        # Flag weak sub-scores
        if tch_summary.explanation_score < 60.0:
            bundle.candidates.append(
                EvidenceCandidate(
                    source="teaching",
                    decision_type="WEAK_EXPLANATION",
                    decision_id=tch_analysis.id,
                    subject="Explanation Quality",
                    description=(
                        f"Explanation score is {tch_summary.explanation_score:.1f}/100, "
                        f"below the 60.0 threshold"
                    ),
                    metric_name="explanation_score",
                    metric_value=tch_summary.explanation_score,
                )
            )
        if tch_summary.interaction_score < 40.0:
            bundle.candidates.append(
                EvidenceCandidate(
                    source="teaching",
                    decision_type="LOW_INTERACTION",
                    decision_id=tch_analysis.id,
                    subject="Classroom Interaction",
                    description=(
                        f"Interaction score is {tch_summary.interaction_score:.1f}/100, "
                        f"below the 40.0 threshold"
                    ),
                    metric_name="interaction_score",
                    metric_value=tch_summary.interaction_score,
                )
            )
        if tch_summary.structure_score < 50.0:
            bundle.candidates.append(
                EvidenceCandidate(
                    source="teaching",
                    decision_type="POOR_STRUCTURE",
                    decision_id=tch_analysis.id,
                    subject="Lecture Structure",
                    description=(
                        f"Structure score is {tch_summary.structure_score:.1f}/100, "
                        f"below the 50.0 threshold"
                    ),
                    metric_name="structure_score",
                    metric_value=tch_summary.structure_score,
                )
            )

    # ── Recommendations ──────────────────────────────────────────────────────

    def _collect_recommendations(self, lecture_id: UUID, bundle: CollectedEvidence) -> None:
        rec_analysis = (
            self.db.query(RecAnalysis)
            .filter(RecAnalysis.lecture_id == lecture_id, RecAnalysis.is_active == True)
            .first()
        )
        if not rec_analysis:
            return
        bundle.rec_analysis_id = rec_analysis.id

        high_priority_items = (
            self.db.query(RecItem)
            .filter(
                RecItem.analysis_id == rec_analysis.id,
                RecItem.priority_level.in_(("CRITICAL", "HIGH")),
            )
            .all()
        )
        for ri in high_priority_items:
            bundle.candidates.append(
                EvidenceCandidate(
                    source="recommendation",
                    decision_type=f"RECOMMENDATION_{ri.priority_level}",
                    decision_id=ri.id,
                    subject=ri.title,
                    description=f"Priority {ri.priority_level}: {ri.recommended_action}",
                    metric_name="priority_score",
                    metric_value=ri.priority_score,
                )
            )
