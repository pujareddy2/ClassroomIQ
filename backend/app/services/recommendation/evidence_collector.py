"""
Module 1: Evidence Collector

Collects raw facts and weaknesses from previous AI module summaries in PostgreSQL.
Does NOT generate recommendations or use LLMs — purely aggregates evidence facts.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.coverage_result import CoverageResult
from app.models.coverage_summary import CoverageSummary
from app.models.teaching_intelligence import (
    TeachingAnalysis,
    TeachingExplanation,
    TeachingInteraction,
    TeachingStructure,
    TeachingSummary,
)
from app.models.validation_result import ValidationResult
from app.models.validation_summary import ValidationSummary


@dataclass
class EvidenceFact:
    source: str                    # "coverage" | "validation" | "teaching"
    evidence_type: str            # e.g. "SKIPPED_TOPIC", "FORMULA_ERROR", "LOW_INTERACTION"
    description: str
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    topic_name: Optional[str] = None
    severity_level: str = "MEDIUM" # "HIGH", "MEDIUM", "LOW"


@dataclass
class EvidenceBundle:
    lecture_id: UUID
    coverage_summary_id: Optional[UUID] = None
    validation_summary_id: Optional[UUID] = None
    teaching_analysis_id: Optional[UUID] = None
    faculty_id: Optional[UUID] = None
    curriculum_id: Optional[UUID] = None

    coverage_facts: List[EvidenceFact] = field(default_factory=list)
    validation_facts: List[EvidenceFact] = field(default_factory=list)
    teaching_facts: List[EvidenceFact] = field(default_factory=list)

    # Raw metrics for fast rule evaluation
    weighted_coverage_pct: float = 100.0
    skipped_topics_count: int = 0
    formula_errors_count: int = 0
    code_errors_count: int = 0
    incorrect_concepts_count: int = 0
    explanation_score: float = 100.0
    example_score: float = 100.0
    structure_score: float = 100.0
    interaction_score: float = 100.0


class EvidenceCollector:

    def __init__(self, db: Session):
        self.db = db

    def collect(
        self,
        lecture_id: UUID,
        coverage_summary: Optional[CoverageSummary] = None,
        validation_summary: Optional[ValidationSummary] = None,
        teaching_summary: Optional[TeachingSummary] = None,
        teaching_analysis: Optional[TeachingAnalysis] = None,
    ) -> EvidenceBundle:
        """Collect all evidence facts for a lecture from DB summaries and detailed results."""

        # Auto-fetch summaries from DB if not passed directly
        if not coverage_summary:
            coverage_summary = (
                self.db.query(CoverageSummary)
                .filter(CoverageSummary.lecture_id == lecture_id, CoverageSummary.status == "ACTIVE")
                .first()
            )

        if not validation_summary:
            validation_summary = (
                self.db.query(ValidationSummary)
                .filter(ValidationSummary.lecture_id == lecture_id, ValidationSummary.status == "ACTIVE")
                .first()
            )

        if not teaching_analysis:
            teaching_analysis = (
                self.db.query(TeachingAnalysis)
                .filter(TeachingAnalysis.lecture_id == lecture_id, TeachingAnalysis.is_active == True)
                .first()
            )

        if teaching_analysis and not teaching_summary:
            teaching_summary = (
                self.db.query(TeachingSummary)
                .filter(TeachingSummary.analysis_id == teaching_analysis.id)
                .first()
            )

        bundle = EvidenceBundle(
            lecture_id=lecture_id,
            coverage_summary_id=coverage_summary.id if coverage_summary else None,
            validation_summary_id=validation_summary.id if validation_summary else None,
            teaching_analysis_id=teaching_analysis.id if teaching_analysis else None,
            faculty_id=teaching_analysis.faculty_id if teaching_analysis else None,
            curriculum_id=coverage_summary.curriculum_id if coverage_summary else None,
        )

        # ── 1. Collect Coverage Evidence ──────────────────────────────────────
        if coverage_summary:
            bundle.weighted_coverage_pct = coverage_summary.weighted_coverage_percentage
            bundle.skipped_topics_count = coverage_summary.skipped_topics

            if coverage_summary.weighted_coverage_percentage < 70.0:
                bundle.coverage_facts.append(
                    EvidenceFact(
                        source="coverage",
                        evidence_type="LOW_COVERAGE",
                        description=f"Weighted curriculum coverage is {coverage_summary.weighted_coverage_percentage:.1f}%, below target threshold of 70.0%",
                        metric_name="weighted_coverage_percentage",
                        metric_value=coverage_summary.weighted_coverage_percentage,
                        threshold=70.0,
                        severity_level="HIGH" if coverage_summary.weighted_coverage_percentage < 50.0 else "MEDIUM",
                    )
                )

            if coverage_summary.skipped_topics > 0:
                bundle.coverage_facts.append(
                    EvidenceFact(
                        source="coverage",
                        evidence_type="SKIPPED_TOPICS",
                        description=f"{coverage_summary.skipped_topics} scheduled topic(s) were completely skipped during lecture",
                        metric_name="skipped_topics",
                        metric_value=float(coverage_summary.skipped_topics),
                        threshold=0.0,
                        severity_level="HIGH" if coverage_summary.skipped_topics >= 3 else "MEDIUM",
                    )
                )

            if coverage_summary.rushed_topics > 0:
                bundle.coverage_facts.append(
                    EvidenceFact(
                        source="coverage",
                        evidence_type="RUSHED_TOPICS",
                        description=f"{coverage_summary.rushed_topics} topic(s) were rushed through significantly faster than expected duration",
                        metric_name="rushed_topics",
                        metric_value=float(coverage_summary.rushed_topics),
                        threshold=0.0,
                        severity_level="LOW",
                    )
                )

            # Query detailed skipped/rushed topic names from CoverageResult table
            detailed_results = (
                self.db.query(CoverageResult)
                .filter(CoverageResult.lecture_id == lecture_id, CoverageResult.status == "ACTIVE")
                .all()
            )
            for res in detailed_results:
                if res.coverage_status == "SKIPPED":
                    bundle.coverage_facts.append(
                        EvidenceFact(
                            source="coverage",
                            evidence_type="SKIPPED_TOPIC_ITEM",
                            description=f"Topic '{res.topic_name}' was completely skipped",
                            topic_name=res.topic_name,
                            severity_level="HIGH",
                        )
                    )

        # ── 2. Collect Validation Evidence ────────────────────────────────────
        if validation_summary:
            bundle.formula_errors_count = validation_summary.formula_issues
            bundle.code_errors_count = validation_summary.code_issues
            bundle.incorrect_concepts_count = validation_summary.incorrect_concepts

            if validation_summary.formula_issues > 0:
                bundle.validation_facts.append(
                    EvidenceFact(
                        source="validation",
                        evidence_type="FORMULA_ERRORS",
                        description=f"Detected {validation_summary.formula_issues} mathematical formula or derivation error(s)",
                        metric_name="formula_issues",
                        metric_value=float(validation_summary.formula_issues),
                        threshold=0.0,
                        severity_level="HIGH" if validation_summary.formula_issues > 2 else "MEDIUM",
                    )
                )

            if validation_summary.incorrect_concepts > 0:
                bundle.validation_facts.append(
                    EvidenceFact(
                        source="validation",
                        evidence_type="INCORRECT_CONCEPTS",
                        description=f"Detected {validation_summary.incorrect_concepts} factually incorrect or inaccurate conceptual statement(s)",
                        metric_name="incorrect_concepts",
                        metric_value=float(validation_summary.incorrect_concepts),
                        threshold=0.0,
                        severity_level="CRITICAL" if validation_summary.incorrect_concepts >= 3 else "HIGH",
                    )
                )

            if validation_summary.code_issues > 0:
                bundle.validation_facts.append(
                    EvidenceFact(
                        source="validation",
                        evidence_type="CODE_ERRORS",
                        description=f"Detected {validation_summary.code_issues} programming code logic or syntax error(s)",
                        metric_name="code_issues",
                        metric_value=float(validation_summary.code_issues),
                        threshold=0.0,
                        severity_level="MEDIUM",
                    )
                )

            if validation_summary.terminology_errors > 0:
                bundle.validation_facts.append(
                    EvidenceFact(
                        source="validation",
                        evidence_type="TERMINOLOGY_ERRORS",
                        description=f"Detected {validation_summary.terminology_errors} imprecise domain terminology usage instance(s)",
                        metric_name="terminology_errors",
                        metric_value=float(validation_summary.terminology_errors),
                        threshold=0.0,
                        severity_level="LOW",
                    )
                )

            # Query detailed incorrect concept topic names
            val_results = (
                self.db.query(ValidationResult)
                .filter(ValidationResult.lecture_id == lecture_id, ValidationResult.status == "ACTIVE")
                .all()
            )
            for vr in val_results:
                if vr.validation_status in ("INCORRECT", "FORMULA_ERROR", "CODE_ERROR"):
                    bundle.validation_facts.append(
                        EvidenceFact(
                            source="validation",
                            evidence_type=f"DETAILED_{vr.validation_status}",
                            description=f"Issue in chunk [{vr.chunk_id}]: {vr.reason}",
                            severity_level=vr.severity,
                        )
                    )

        # ── 3. Collect Teaching Intelligence Evidence ─────────────────────────
        if teaching_summary:
            bundle.explanation_score = teaching_summary.explanation_score
            bundle.example_score = teaching_summary.example_score
            bundle.structure_score = teaching_summary.structure_score
            bundle.interaction_score = teaching_summary.interaction_score

            if teaching_summary.explanation_score < 60.0:
                bundle.teaching_facts.append(
                    EvidenceFact(
                        source="teaching",
                        evidence_type="WEAK_EXPLANATION",
                        description=f"Explanation quality score is {teaching_summary.explanation_score:.1f}/100, below target threshold of 60.0",
                        metric_name="explanation_score",
                        metric_value=teaching_summary.explanation_score,
                        threshold=60.0,
                        severity_level="HIGH" if teaching_summary.explanation_score < 40.0 else "MEDIUM",
                    )
                )

            if teaching_summary.example_score < 60.0:
                bundle.teaching_facts.append(
                    EvidenceFact(
                        source="teaching",
                        evidence_type="LOW_EXAMPLES",
                        description=f"Real-world example score is {teaching_summary.example_score:.1f}/100, indicating insufficient illustrative examples",
                        metric_name="example_score",
                        metric_value=teaching_summary.example_score,
                        threshold=60.0,
                        severity_level="MEDIUM",
                    )
                )

            if teaching_summary.structure_score < 60.0:
                bundle.teaching_facts.append(
                    EvidenceFact(
                        source="teaching",
                        evidence_type="POOR_STRUCTURE",
                        description=f"Lecture structure score is {teaching_summary.structure_score:.1f}/100, indicating organization or flow issues",
                        metric_name="structure_score",
                        metric_value=teaching_summary.structure_score,
                        threshold=60.0,
                        severity_level="MEDIUM",
                    )
                )

            if teaching_summary.interaction_score < 40.0:
                bundle.teaching_facts.append(
                    EvidenceFact(
                        source="teaching",
                        evidence_type="LOW_INTERACTION",
                        description=f"Classroom interaction score is {teaching_summary.interaction_score:.1f}/100, indicating low student engagement",
                        metric_name="interaction_score",
                        metric_value=teaching_summary.interaction_score,
                        threshold=40.0,
                        severity_level="HIGH" if teaching_summary.interaction_score < 20.0 else "MEDIUM",
                    )
                )

            # Query detailed structure & interaction facts if available
            if teaching_analysis:
                ts = (
                    self.db.query(TeachingStructure)
                    .filter(TeachingStructure.analysis_id == teaching_analysis.id)
                    .first()
                )
                if ts:
                    if not ts.has_introduction:
                        bundle.teaching_facts.append(
                            EvidenceFact(
                                source="teaching",
                                evidence_type="MISSING_INTRO",
                                description="Lecture lacked a clear introductory roadmap overview",
                                severity_level="MEDIUM",
                            )
                        )
                    if not ts.has_conclusion:
                        bundle.teaching_facts.append(
                            EvidenceFact(
                                source="teaching",
                                evidence_type="MISSING_CONCLUSION",
                                description="Lecture ended abruptly without a summary or recap conclusion",
                                severity_level="LOW",
                            )
                        )

                ti = (
                    self.db.query(TeachingInteraction)
                    .filter(TeachingInteraction.analysis_id == teaching_analysis.id)
                    .first()
                )
                if ti and ti.faculty_question_count == 0:
                    bundle.teaching_facts.append(
                        EvidenceFact(
                            source="teaching",
                            evidence_type="NO_FACULTY_QUESTIONS",
                            description="Faculty asked zero interactive checks for understanding during the lecture",
                            severity_level="HIGH",
                        )
                    )

        return bundle
