"""
Module 2: Recommendation Rule Engine

Purely deterministic IF-THEN rules that evaluate an EvidenceBundle and produce
RawRecommendation objects. Does NOT use LLMs.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.services.recommendation.evidence_collector import EvidenceBundle, EvidenceFact


@dataclass
class RawRecommendation:
    recommendation_type: str
    category: str              # "Coverage" | "Validation" | "Pedagogical"
    title: str
    reason: str
    recommended_action: str
    severity: float = 50.0      # 0-100
    impact: float = 50.0        # 0-100
    urgency: float = 50.0       # 0-100
    confidence: float = 85.0    # 0-100
    supporting_facts: List[EvidenceFact] = field(default_factory=list)


class RecommendationRuleEngine:

    def evaluate(self, bundle: EvidenceBundle) -> List[RawRecommendation]:
        """Evaluate evidence bundle against deterministic recommendation rules."""
        raw_recs: List[RawRecommendation] = []

        # Rule 1: Coverage < 70%
        if bundle.weighted_coverage_pct < 70.0:
            cov_facts = [f for f in bundle.coverage_facts if f.evidence_type == "LOW_COVERAGE"]
            raw_recs.append(
                RawRecommendation(
                    recommendation_type="IMPROVE_CURRICULUM_COVERAGE",
                    category="Coverage",
                    title="Improve Overall Curriculum Coverage",
                    reason=f"Weighted curriculum coverage for this lecture was only {bundle.weighted_coverage_pct:.1f}%, below the target 70.0%.",
                    recommended_action="Pace lecture delivery to ensure all planned curriculum topics receive adequate instructional time.",
                    severity=80.0 if bundle.weighted_coverage_pct < 50.0 else 65.0,
                    impact=85.0,
                    urgency=75.0,
                    confidence=95.0,
                    supporting_facts=cov_facts,
                )
            )

        # Rule 2: Skipped Topics > 0
        if bundle.skipped_topics_count > 0:
            skipped_facts = [f for f in bundle.coverage_facts if f.evidence_type in ("SKIPPED_TOPICS", "SKIPPED_TOPIC_ITEM")]
            topic_names = [f.topic_name for f in skipped_facts if f.topic_name]
            topics_str = f" ({', '.join(topic_names[:3])})" if topic_names else ""

            raw_recs.append(
                RawRecommendation(
                    recommendation_type="TEACH_SKIPPED_TOPICS",
                    category="Coverage",
                    title=f"Schedule and Teach Skipped Topics{topics_str}",
                    reason=f"{bundle.skipped_topics_count} scheduled topic(s) were completely omitted during the lecture session.",
                    recommended_action="Dedicate the beginning of the next class or a recap session to cover the skipped curriculum topics.",
                    severity=85.0 if bundle.skipped_topics_count >= 3 else 70.0,
                    impact=90.0,
                    urgency=80.0,
                    confidence=95.0,
                    supporting_facts=skipped_facts,
                )
            )

        # Rule 3: Formula Errors > 2 (or > 0)
        if bundle.formula_errors_count > 0:
            formula_facts = [f for f in bundle.validation_facts if f.evidence_type == "FORMULA_ERRORS"]
            raw_recs.append(
                RawRecommendation(
                    recommendation_type="REVIEW_MATHEMATICAL_DERIVATIONS",
                    category="Validation",
                    title="Review Mathematical Derivations and Formulas",
                    reason=f"Detected {bundle.formula_errors_count} mathematical notation or derivation error(s) during lecture delivery.",
                    recommended_action="Review board work and slide formulas before lecture; issue a brief correction note to students if formulas were transcribed incorrectly.",
                    severity=90.0 if bundle.formula_errors_count > 2 else 75.0,
                    impact=85.0,
                    urgency=85.0,
                    confidence=90.0,
                    supporting_facts=formula_facts,
                )
            )

        # Rule 4: Incorrect Concepts > 0
        if bundle.incorrect_concepts_count > 0:
            inc_facts = [f for f in bundle.validation_facts if f.evidence_type == "INCORRECT_CONCEPTS"]
            raw_recs.append(
                RawRecommendation(
                    recommendation_type="CORRECT_CONCEPTUAL_ACCURACY",
                    category="Validation",
                    title="Address Factual Inaccuracies and Conceptual Misstatements",
                    reason=f"Detected {bundle.incorrect_concepts_count} factually inaccurate statement(s) that conflict with verified reference materials.",
                    recommended_action="Provide a clarification at the start of the next lecture to prevent student misconceptions regarding these core concepts.",
                    severity=95.0,
                    impact=95.0,
                    urgency=90.0,
                    confidence=92.0,
                    supporting_facts=inc_facts,
                )
            )

        # Rule 5: Code Errors > 0
        if bundle.code_errors_count > 0:
            code_facts = [f for f in bundle.validation_facts if f.evidence_type == "CODE_ERRORS"]
            raw_recs.append(
                RawRecommendation(
                    recommendation_type="VERIFY_PROGRAMMING_CODE",
                    category="Validation",
                    title="Verify Programming Syntax and Live Code Demos",
                    reason=f"Detected {bundle.code_errors_count} syntax or logical issue(s) in code snippets demonstrated during the lecture.",
                    recommended_action="Test all live code examples in an IDE prior to lecture and share working repository links with students.",
                    severity=70.0,
                    impact=75.0,
                    urgency=65.0,
                    confidence=88.0,
                    supporting_facts=code_facts,
                )
            )

        # Rule 6: Explanation Score < 60
        if bundle.explanation_score < 60.0:
            exp_facts = [f for f in bundle.teaching_facts if f.evidence_type == "WEAK_EXPLANATION"]
            raw_recs.append(
                RawRecommendation(
                    recommendation_type="IMPROVE_EXPLANATION_QUALITY",
                    category="Pedagogical",
                    title="Enhance Step-by-Step Explanation Clarity",
                    reason=f"Explanation quality score is {bundle.explanation_score:.1f}/100, indicating room for clearer step-by-step breakdowns.",
                    recommended_action="Deconstruct complex theoretical concepts into incremental steps and check for understanding between progression phases.",
                    severity=75.0 if bundle.explanation_score < 40.0 else 60.0,
                    impact=80.0,
                    urgency=70.0,
                    confidence=85.0,
                    supporting_facts=exp_facts,
                )
            )

        # Rule 7: Example Score < 60
        if bundle.example_score < 60.0:
            ex_facts = [f for f in bundle.teaching_facts if f.evidence_type == "LOW_EXAMPLES"]
            raw_recs.append(
                RawRecommendation(
                    recommendation_type="ADD_REAL_WORLD_EXAMPLES",
                    category="Pedagogical",
                    title="Incorporate Real-World Examples and Practical Demos",
                    reason=f"Example score is {bundle.example_score:.1f}/100, indicating theoretical explanations were delivered with few practical illustrations.",
                    recommended_action="Include at least two concrete real-world applications or industrial case studies for each major topic.",
                    severity=60.0,
                    impact=75.0,
                    urgency=60.0,
                    confidence=85.0,
                    supporting_facts=ex_facts,
                )
            )

        # Rule 8: Interaction Score < 40
        if bundle.interaction_score < 40.0:
            int_facts = [f for f in bundle.teaching_facts if f.evidence_type in ("LOW_INTERACTION", "NO_FACULTY_QUESTIONS")]
            raw_recs.append(
                RawRecommendation(
                    recommendation_type="INCREASE_CLASSROOM_INTERACTION",
                    category="Pedagogical",
                    title="Boost Student Engagement and Active Questioning",
                    reason=f"Interaction score is {bundle.interaction_score:.1f}/100, indicating limited active dialogue or student participation.",
                    recommended_action="Incorporate Socratic questioning, short think-pair-share prompts, or quick polling to check comprehension during delivery.",
                    severity=80.0 if bundle.interaction_score < 20.0 else 65.0,
                    impact=85.0,
                    urgency=75.0,
                    confidence=90.0,
                    supporting_facts=int_facts,
                )
            )

        # Rule 9: Structure Score < 60
        if bundle.structure_score < 60.0:
            struct_facts = [f for f in bundle.teaching_facts if f.evidence_type in ("POOR_STRUCTURE", "MISSING_INTRO", "MISSING_CONCLUSION")]
            raw_recs.append(
                RawRecommendation(
                    recommendation_type="IMPROVE_LECTURE_ORGANIZATION",
                    category="Pedagogical",
                    title="Improve Lecture Structure and Transition Signals",
                    reason=f"Lecture structure score is {bundle.structure_score:.1f}/100, indicating abrupt topic transitions or missing overview framing.",
                    recommended_action="Begin each lecture with a clear agenda outline, use explicit transition phrases between topics, and close with a key takeaway recap.",
                    severity=65.0,
                    impact=75.0,
                    urgency=60.0,
                    confidence=85.0,
                    supporting_facts=struct_facts,
                )
            )

        return raw_recs
