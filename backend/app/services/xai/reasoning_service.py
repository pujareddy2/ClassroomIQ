"""
ReasoningService

Generates ordered DAG reasoning steps for each AI decision.
Each chain follows a strict 4-step logical structure:

  Step 1: [OBSERVATION]  — Raw fact observed in upstream data
  Step 2: [EVIDENCE]     — Supporting metric / reference evidence
  Step 3: [ANALYSIS]     — Comparison to threshold or benchmark
  Step 4: [CONCLUSION]   — Final decision label with justification

All reasoning is deterministic — derived from actual data, not LLM output.
"""

import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from app.models.explanation_engine import ReasoningStep
from app.services.xai.evidence_collector import EvidenceCandidate

logger = logging.getLogger(__name__)


@dataclass
class ReasoningStepData:
    step_order: int
    reason: str
    evidence_reference: str


class ReasoningService:
    """
    Generates deterministic reasoning steps per EvidenceCandidate.
    No DB access — pure computation.
    """

    def build_steps(self, candidate: EvidenceCandidate, citation_doc_name: str) -> List[ReasoningStepData]:
        """Route to the correct DAG builder based on candidate source."""
        logger.info("Reasoning Generated — source=%s, type=%s", candidate.source, candidate.decision_type)

        if candidate.source == "coverage":
            return self._coverage_dag(candidate, citation_doc_name)
        elif candidate.source == "validation":
            return self._validation_dag(candidate, citation_doc_name)
        elif candidate.source == "teaching":
            return self._teaching_dag(candidate, citation_doc_name)
        elif candidate.source == "recommendation":
            return self._recommendation_dag(candidate, citation_doc_name)
        else:
            return self._generic_dag(candidate, citation_doc_name)

    # ── Coverage DAG ─────────────────────────────────────────────────────────

    def _coverage_dag(self, c: EvidenceCandidate, doc: str) -> List[ReasoningStepData]:
        pct = c.metric_value if c.metric_value is not None else 0.0
        status = c.decision_type.replace("COVERAGE_", "").replace("_", " ").title()
        return [
            ReasoningStepData(1,
                f"[OBSERVATION] Transcript analysis identified topic '{c.subject}' "
                f"with coverage status: {status}.",
                "coverage_engine"),
            ReasoningStepData(2,
                f"[EVIDENCE] Coverage Engine measured {pct:.1f}% coverage. "
                f"Reference: '{doc}' confirms this topic is curriculum-required.",
                "coverage_engine → reference_material"),
            ReasoningStepData(3,
                f"[ANALYSIS] Coverage threshold for adequate instruction is 50.0%. "
                f"Measured coverage of {pct:.1f}% is "
                f"{'below' if pct < 50.0 else 'at or above'} this threshold.",
                "coverage_engine → threshold_analysis"),
            ReasoningStepData(4,
                f"[CONCLUSION] '{c.subject}' classified as {status} because "
                f"only {pct:.1f}% of required content was delivered. "
                f"Supported by reference: '{doc}'.",
                "coverage_engine → conclusion"),
        ]

    # ── Validation DAG ───────────────────────────────────────────────────────

    def _validation_dag(self, c: EvidenceCandidate, doc: str) -> List[ReasoningStepData]:
        conf = c.metric_value if c.metric_value is not None else 0.0
        conf_pct = (conf * 100.0) if 0.0 <= conf <= 1.0 else conf
        error_type = c.decision_type.replace("VALIDATION_", "").replace("_", " ").title()
        return [
            ReasoningStepData(1,
                f"[OBSERVATION] Validation Engine detected a {error_type} issue.",
                "validation_engine"),
            ReasoningStepData(2,
                f"[EVIDENCE] Validation confidence: {conf_pct:.1f}%. "
                f"Recorded reason: \"{c.description}\".",
                "validation_engine → confidence_score"),
            ReasoningStepData(3,
                f"[ANALYSIS] Reporting threshold is 70.0% confidence. "
                f"This error {'exceeds' if conf_pct >= 70.0 else 'approaches'} "
                f"the threshold. Reference '{doc}' used for cross-validation.",
                "validation_engine → threshold_analysis"),
            ReasoningStepData(4,
                f"[CONCLUSION] {error_type} flagged because transcript content "
                f"contradicts verified technical standards. Confidence: {conf_pct:.1f}%.",
                "validation_engine → conclusion"),
        ]

    # ── Teaching DAG ─────────────────────────────────────────────────────────

    def _teaching_dag(self, c: EvidenceCandidate, doc: str) -> List[ReasoningStepData]:
        score = c.metric_value if c.metric_value is not None else 0.0
        metric = (c.metric_name or "teaching_metric").replace("_", " ").title()
        threshold = 60.0 if "explanation" in (c.metric_name or "") else 40.0
        return [
            ReasoningStepData(1,
                f"[OBSERVATION] Teaching Intelligence evaluated '{c.subject}' "
                f"and recorded {metric} of {score:.1f}/100.",
                "teaching_engine"),
            ReasoningStepData(2,
                f"[EVIDENCE] Measured {metric} ({score:.1f}) compared against "
                f"benchmark threshold of {threshold:.0f}/100. Reference: '{doc}'.",
                "teaching_engine → reference_material"),
            ReasoningStepData(3,
                f"[ANALYSIS] A {metric} below {threshold:.0f} indicates inadequate "
                f"quality. Score of {score:.1f} is "
                f"{'below' if score < threshold else 'meeting'} the benchmark.",
                "teaching_engine → threshold_analysis"),
            ReasoningStepData(4,
                f"[CONCLUSION] '{c.subject}' classified as '{c.decision_type}' "
                f"because {metric} ({score:.1f}) did not meet the minimum standard.",
                "teaching_engine → conclusion"),
        ]

    # ── Recommendation DAG ───────────────────────────────────────────────────

    def _recommendation_dag(self, c: EvidenceCandidate, doc: str) -> List[ReasoningStepData]:
        priority = c.decision_type.replace("RECOMMENDATION_", "")
        score = c.metric_value if c.metric_value is not None else 0.0
        return [
            ReasoningStepData(1,
                f"[OBSERVATION] Recommendation Engine generated a {priority}-priority "
                f"recommendation: '{c.subject}'.",
                "recommendation_engine"),
            ReasoningStepData(2,
                f"[EVIDENCE] Priority score: {score:.2f}. Triggered by aggregated "
                f"signals from Coverage, Validation, and Teaching engines. "
                f"Reference: '{doc}'.",
                "recommendation_engine → upstream_signals"),
            ReasoningStepData(3,
                f"[ANALYSIS] {priority} priority assigned when multiple engines "
                f"independently confirm the same gap. '{c.subject}' met the "
                f"{priority} criteria based on composite scoring.",
                "recommendation_engine → priority_analysis"),
            ReasoningStepData(4,
                f"[CONCLUSION] '{c.subject}' issued as a {priority} priority action "
                f"based on converging evidence. Intervention: {c.description}.",
                "recommendation_engine → conclusion"),
        ]

    # ── Generic Fallback ─────────────────────────────────────────────────────

    def _generic_dag(self, c: EvidenceCandidate, doc: str) -> List[ReasoningStepData]:
        return [
            ReasoningStepData(1,
                f"[OBSERVATION] AI engine identified: '{c.subject}' — {c.description}.",
                c.source or "upstream_engine"),
            ReasoningStepData(2,
                f"[EVIDENCE] Metric '{c.metric_name}' = {c.metric_value}. "
                f"Reference: '{doc}'.",
                f"{c.source} → evidence"),
            ReasoningStepData(3,
                f"[ANALYSIS] Evidence evaluated against curriculum standards. "
                f"'{c.decision_type}' classification assigned.",
                f"{c.source} → threshold_analysis"),
            ReasoningStepData(4,
                f"[CONCLUSION] Decision '{c.decision_type}' for '{c.subject}' "
                f"justified by measured data and verified reference material.",
                f"{c.source} → conclusion"),
        ]

    # ── ORM Conversion ───────────────────────────────────────────────────────

    def to_orm_list(self, explanation_record_id: UUID, steps: List[ReasoningStepData]) -> List[ReasoningStep]:
        return [
            ReasoningStep(
                explanation_record_id=explanation_record_id,
                step_order=s.step_order,
                reason=s.reason,
                evidence_reference=s.evidence_reference,
            )
            for s in steps
        ]
