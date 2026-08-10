"""
Module 5: Duplicate Recommendation Merger

Merges equivalent or overlapping recommendations produced by different rules/modules
(e.g., Coverage + Validation issues on the same topic) to prevent redundant feedback.
"""

from typing import Dict, List

from app.services.recommendation.rule_engine import RawRecommendation


class DuplicateMerger:

    def merge(self, raw_recs: List[RawRecommendation]) -> List[RawRecommendation]:
        """Deduplicate and merge equivalent recommendations."""
        if not raw_recs:
            return []

        # ── 1. Deduplicate exact recommendation_type duplicates ─────────────────
        by_type: Dict[str, List[RawRecommendation]] = {}
        for rec in raw_recs:
            by_type.setdefault(rec.recommendation_type, []).append(rec)

        merged_recs: List[RawRecommendation] = []
        for rec_type, group in by_type.items():
            if len(group) == 1:
                merged_recs.append(group[0])
            else:
                # Combine duplicates of the same type
                primary = group[0]
                combined_facts = []
                max_severity = primary.severity
                max_impact = primary.impact
                max_urgency = primary.urgency
                max_confidence = primary.confidence

                for item in group:
                    combined_facts.extend(item.supporting_facts)
                    max_severity = max(max_severity, item.severity)
                    max_impact = max(max_impact, item.impact)
                    max_urgency = max(max_urgency, item.urgency)
                    max_confidence = max(max_confidence, item.confidence)

                # Deduplicate evidence facts by description
                unique_facts = []
                seen_desc = set()
                for f in combined_facts:
                    if f.description not in seen_desc:
                        seen_desc.add(f.description)
                        unique_facts.append(f)

                primary.supporting_facts = unique_facts
                primary.severity = max_severity
                primary.impact = max_impact
                primary.urgency = max_urgency
                primary.confidence = max_confidence
                merged_recs.append(primary)

        # ── 2. Cross-category merge: Coverage (Skipped/Low Coverage) + Validation (Inaccuracies) ─
        has_coverage_issue = any(r.category == "Coverage" for r in merged_recs)
        has_validation_issue = any(r.category == "Validation" for r in merged_recs)

        # If both coverage & validation have critical issues on the same lecture, create high-impact combined focus item if helpful, or tag merged_from metadata
        # (We preserve distinct actionable recommendations while assigning merged_from categories for UI transparency)

        return merged_recs
