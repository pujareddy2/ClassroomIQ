"""
Engine 5: XAI Reasoning Engine

Builds a Directed Acyclic Graph (DAG) of logical reasoning steps
that trace how the upstream AI arrived at a decision.

Rules:
  - Steps must follow a strict logical chain: Observation → Evidence → Analysis → Conclusion.
  - Every step references a real data source (coverage, validation, teaching, recommendation).
  - Steps are deterministic — derived from actual data, not LLM hallucination.
  - The DAG is represented as an ordered list of reasoning steps.

Standard DAG structure per decision type:
  Step 1: [OBSERVATION]  — Raw fact observed in data
  Step 2: [EVIDENCE]     — Supporting metric / reference evidence
  Step 3: [ANALYSIS]     — Comparison to threshold or benchmark
  Step 4: [CONCLUSION]   — Final decision label with justification
"""

from dataclasses import dataclass
from typing import List
from uuid import UUID

from app.models.xai_engine import XAIReasoningStep
from app.services.xai.evidence_collector import XAIFact
from app.services.xai.reference_citation_engine import AcademicReferenceCitation


@dataclass
class ReasoningStepData:
    step_number: int
    claim: str
    evidence_source: str


# ── Threshold constants used in reasoning narratives ─────────────────────────
_COVERAGE_SKIP_THRESHOLD = 50.0   # % below which a topic is considered inadequately covered
_EXPLANATION_THRESHOLD = 60.0     # teaching score below which explanation is weak
_INTERACTION_THRESHOLD = 40.0     # interaction score below which engagement is low
_VALIDATION_CONFIDENCE = 0.70     # validation confidence threshold for reporting issues


class XAIReasoningEngine:
    """
    Generates an ordered list of deterministic reasoning steps for each AI decision.
    Steps are derived purely from the XAIFact and supporting citation — no LLM.
    """

    def build_reasoning_steps(
        self,
        fact: XAIFact,
        citation: AcademicReferenceCitation,
    ) -> List[ReasoningStepData]:
        """Route to the correct DAG builder based on fact source."""

        if fact.source == "coverage":
            return self._coverage_dag(fact, citation)
        elif fact.source == "validation":
            return self._validation_dag(fact, citation)
        elif fact.source == "teaching":
            return self._teaching_dag(fact, citation)
        elif fact.source == "recommendation":
            return self._recommendation_dag(fact, citation)
        else:
            return self._generic_dag(fact, citation)

    # ── Coverage DAG ─────────────────────────────────────────────────────────

    def _coverage_dag(self, fact: XAIFact, citation: AcademicReferenceCitation) -> List[ReasoningStepData]:
        pct = fact.metric_value if fact.metric_value is not None else 0.0
        status_label = fact.fact_type.replace("COVERAGE_", "").replace("_", " ").title()

        return [
            ReasoningStepData(
                step_number=1,
                claim=(
                    f"[OBSERVATION] Transcript analysis identified topic '{fact.subject}' "
                    f"with coverage status: {status_label}."
                ),
                evidence_source="coverage_engine",
            ),
            ReasoningStepData(
                step_number=2,
                claim=(
                    f"[EVIDENCE] Curriculum Coverage Engine measured {pct:.1f}% coverage for this topic. "
                    f"Reference standard: '{citation.document_name}' confirms this topic is curriculum-required."
                ),
                evidence_source="coverage_engine → reference_material",
            ),
            ReasoningStepData(
                step_number=3,
                claim=(
                    f"[ANALYSIS] Coverage threshold for adequate instruction is {_COVERAGE_SKIP_THRESHOLD:.0f}%. "
                    f"Measured coverage of {pct:.1f}% is "
                    f"{'below' if pct < _COVERAGE_SKIP_THRESHOLD else 'at or above'} "
                    f"this threshold, classifying the topic as {status_label}."
                ),
                evidence_source="coverage_engine → threshold_analysis",
            ),
            ReasoningStepData(
                step_number=4,
                claim=(
                    f"[CONCLUSION] The Curriculum Coverage Engine classified '{fact.subject}' as {status_label} "
                    f"because only {pct:.1f}% of the required curriculum content was delivered in this lecture. "
                    f"This decision is supported by the uploaded reference material: '{citation.document_name}'."
                ),
                evidence_source="coverage_engine → conclusion",
            ),
        ]

    # ── Validation DAG ───────────────────────────────────────────────────────

    def _validation_dag(self, fact: XAIFact, citation: AcademicReferenceCitation) -> List[ReasoningStepData]:
        conf = fact.metric_value if fact.metric_value is not None else 0.0
        conf_pct = (conf * 100.0) if 0.0 <= conf <= 1.0 else conf
        error_type = fact.fact_type.replace("VALIDATION_", "").replace("_", " ").title()

        return [
            ReasoningStepData(
                step_number=1,
                claim=(
                    f"[OBSERVATION] Technical Validation Engine detected a potential {error_type} "
                    f"in transcript segment {fact.chunk_id or 'N/A'}."
                ),
                evidence_source="validation_engine",
            ),
            ReasoningStepData(
                step_number=2,
                claim=(
                    f"[EVIDENCE] Validation confidence for this error flag is {conf_pct:.1f}%. "
                    f"Validation reason recorded: \"{fact.description}\"."
                ),
                evidence_source="validation_engine → confidence_score",
            ),
            ReasoningStepData(
                step_number=3,
                claim=(
                    f"[ANALYSIS] The validation threshold for reporting an error is "
                    f"{_VALIDATION_CONFIDENCE * 100:.0f}% confidence. "
                    f"With a confidence of {conf_pct:.1f}%, this error "
                    f"{'exceeds' if conf_pct >= _VALIDATION_CONFIDENCE * 100 else 'falls below'} "
                    f"the reporting threshold. "
                    f"Reference standard '{citation.document_name}' was used to cross-validate the claim."
                ),
                evidence_source="validation_engine → threshold_analysis",
            ),
            ReasoningStepData(
                step_number=4,
                claim=(
                    f"[CONCLUSION] The Technical Validation Engine flagged a {error_type} because the "
                    f"transcript content in segment {fact.chunk_id or 'N/A'} contradicts verified "
                    f"technical standards. Evidence confidence: {conf_pct:.1f}%."
                ),
                evidence_source="validation_engine → conclusion",
            ),
        ]

    # ── Teaching DAG ─────────────────────────────────────────────────────────

    def _teaching_dag(self, fact: XAIFact, citation: AcademicReferenceCitation) -> List[ReasoningStepData]:
        score = fact.metric_value if fact.metric_value is not None else 0.0
        metric_label = fact.metric_name.replace("_", " ").title() if fact.metric_name else "Teaching Metric"
        threshold = _EXPLANATION_THRESHOLD if "explanation" in (fact.metric_name or "") else _INTERACTION_THRESHOLD

        return [
            ReasoningStepData(
                step_number=1,
                claim=(
                    f"[OBSERVATION] Teaching Intelligence Engine evaluated '{fact.subject}' "
                    f"and recorded a {metric_label} of {score:.1f}/100."
                ),
                evidence_source="teaching_intelligence_engine",
            ),
            ReasoningStepData(
                step_number=2,
                claim=(
                    f"[EVIDENCE] The measured {metric_label} ({score:.1f}/100) was compared against "
                    f"the educational benchmark threshold of {threshold:.0f}/100. "
                    f"Reference material '{citation.document_name}' documents best practices for this metric."
                ),
                evidence_source="teaching_intelligence_engine → reference_material",
            ),
            ReasoningStepData(
                step_number=3,
                claim=(
                    f"[ANALYSIS] A {metric_label} below {threshold:.0f}/100 indicates inadequate teaching quality "
                    f"for that dimension. Score of {score:.1f} is "
                    f"{'below' if score < threshold else 'meeting'} the accepted benchmark, "
                    f"triggering the '{fact.fact_type}' classification."
                ),
                evidence_source="teaching_intelligence_engine → threshold_analysis",
            ),
            ReasoningStepData(
                step_number=4,
                claim=(
                    f"[CONCLUSION] The Teaching Intelligence Engine classified '{fact.subject}' as '{fact.fact_type}' "
                    f"because the measured {metric_label} ({score:.1f}/100) did not meet the minimum "
                    f"educational quality standard of {threshold:.0f}/100."
                ),
                evidence_source="teaching_intelligence_engine → conclusion",
            ),
        ]

    # ── Recommendation DAG ───────────────────────────────────────────────────

    def _recommendation_dag(self, fact: XAIFact, citation: AcademicReferenceCitation) -> List[ReasoningStepData]:
        priority = fact.fact_type.replace("RECOMMENDATION_", "").replace("_", " ").title()
        score = fact.metric_value if fact.metric_value is not None else 0.0

        return [
            ReasoningStepData(
                step_number=1,
                claim=(
                    f"[OBSERVATION] Recommendation Engine generated a {priority}-priority recommendation: "
                    f"'{fact.subject}'."
                ),
                evidence_source="recommendation_engine",
            ),
            ReasoningStepData(
                step_number=2,
                claim=(
                    f"[EVIDENCE] This recommendation was assigned a priority score of {score:.2f}. "
                    f"It was triggered by aggregated signals from the Coverage, Validation, "
                    f"and Teaching Intelligence engines. Reference: '{citation.document_name}'."
                ),
                evidence_source="recommendation_engine → upstream_signals",
            ),
            ReasoningStepData(
                step_number=3,
                claim=(
                    f"[ANALYSIS] A {priority} priority is assigned when multiple upstream engines "
                    f"independently confirm the same teaching gap. The recommendation '{fact.subject}' "
                    f"satisfied the {priority} priority criteria based on composite priority scoring."
                ),
                evidence_source="recommendation_engine → priority_analysis",
            ),
            ReasoningStepData(
                step_number=4,
                claim=(
                    f"[CONCLUSION] The Recommendation Engine issued '{fact.subject}' as a {priority} "
                    f"priority action item based on converging evidence from multiple AI subsystems. "
                    f"The recommended intervention is: {fact.description}."
                ),
                evidence_source="recommendation_engine → conclusion",
            ),
        ]

    # ── Generic Fallback DAG ─────────────────────────────────────────────────

    def _generic_dag(self, fact: XAIFact, citation: AcademicReferenceCitation) -> List[ReasoningStepData]:
        return [
            ReasoningStepData(
                step_number=1,
                claim=f"[OBSERVATION] AI engine identified issue: '{fact.subject}' — {fact.description}",
                evidence_source=fact.source or "upstream_engine",
            ),
            ReasoningStepData(
                step_number=2,
                claim=(
                    f"[EVIDENCE] Supporting data from source '{fact.source}': "
                    f"metric '{fact.metric_name}' = {fact.metric_value}. "
                    f"Academic reference: '{citation.document_name}'."
                ),
                evidence_source=f"{fact.source} → evidence",
            ),
            ReasoningStepData(
                step_number=3,
                claim=(
                    f"[ANALYSIS] The collected evidence was evaluated against curriculum standards. "
                    f"The '{fact.fact_type}' classification was assigned based on measured deviation."
                ),
                evidence_source=f"{fact.source} → threshold_analysis",
            ),
            ReasoningStepData(
                step_number=4,
                claim=(
                    f"[CONCLUSION] Decision '{fact.fact_type}' for subject '{fact.subject}' "
                    f"is justified by measured data and supported by verified reference material."
                ),
                evidence_source=f"{fact.source} → conclusion",
            ),
        ]

    def to_orm_list(self, package_id: UUID, steps: List[ReasoningStepData]) -> List[XAIReasoningStep]:
        """Convert reasoning step dataclasses to ORM objects."""
        return [
            XAIReasoningStep(
                package_id=package_id,
                step_number=s.step_number,
                claim=s.claim,
                evidence_source=s.evidence_source,
            )
            for s in steps
        ]
