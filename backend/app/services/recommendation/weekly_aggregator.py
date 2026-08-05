"""
Module 6: Weekly Recommendation Aggregator

Aggregates recommendation analyses and metrics across all lectures delivered
by one faculty member within a single academic week (e.g., '2026-W31').
Detects repeated weaknesses, improving/declining trends, and frequent topics.
"""

from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.coverage_summary import CoverageSummary
from app.models.lecture_session import LectureSession
from app.models.recommendation_engine import RecAnalysis, RecItem, RecWeekly
from app.models.teaching_intelligence import TeachingAnalysis, TeachingSummary
from app.models.validation_summary import ValidationSummary


class WeeklyAggregator:

    def __init__(self, db: Session):
        self.db = db

    def aggregate_week(
        self, faculty_id: UUID, week_label: str = "2026-W31"
    ) -> RecWeekly:
        """Aggregate all lecture analyses for a faculty member in a week."""

        # Query all active recommendation analyses for this faculty member
        analyses = (
            self.db.query(RecAnalysis)
            .filter(
                RecAnalysis.faculty_id == faculty_id,
                RecAnalysis.is_active == True,
            )
            .all()
        )

        lecture_count = len(analyses)
        if lecture_count == 0:
            return RecWeekly(
                faculty_id=faculty_id,
                week_label=week_label,
                lecture_count=0,
                total_recommendations=0,
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                repeated_weaknesses=["No lecture analyses recorded this week."],
                improving_areas=[],
                declining_areas=[],
                frequently_skipped_topics=[],
                frequently_incorrect_concepts=[],
                avg_coverage_score=0.0,
                avg_validation_score=0.0,
                avg_teaching_score=0.0,
                summary_text="No active lecture data found for this week.",
            )

        total_recs = sum(a.total_recommendations for a in analyses)
        crit_count = sum(a.critical_count for a in analyses)
        hi_count = sum(a.high_count for a in analyses)
        med_count = sum(a.medium_count for a in analyses)
        lo_count = sum(a.low_count for a in analyses)

        # Collect all items
        analysis_ids = [a.id for a in analyses]
        items = (
            self.db.query(RecItem)
            .filter(RecItem.analysis_id.in_(analysis_ids))
            .all()
        )

        rec_types_counter = Counter(it.recommendation_type for it in items)
        repeated_weaknesses = [
            rtype for rtype, count in rec_types_counter.most_common(5) if count >= 1
        ]

        # Gather average scores from coverage, validation, teaching summaries
        lecture_ids = [a.lecture_id for a in analyses]

        cov_summaries = (
            self.db.query(CoverageSummary)
            .filter(CoverageSummary.lecture_id.in_(lecture_ids), CoverageSummary.status == "ACTIVE")
            .all()
        )
        val_summaries = (
            self.db.query(ValidationSummary)
            .filter(ValidationSummary.lecture_id.in_(lecture_ids), ValidationSummary.status == "ACTIVE")
            .all()
        )
        t_summaries = (
            self.db.query(TeachingSummary)
            .filter(TeachingSummary.lecture_id.in_(lecture_ids))
            .all()
        )

        avg_cov = (
            sum(c.weighted_coverage_percentage for c in cov_summaries) / len(cov_summaries)
            if cov_summaries else 0.0
        )
        avg_val = (
            sum(v.overall_validation_score for v in val_summaries) / len(val_summaries)
            if val_summaries else 0.0
        )
        avg_tch = (
            sum(t.overall_teaching_score for t in t_summaries) / len(t_summaries)
            if t_summaries else 0.0
        )

        # Trend analysis (improving vs declining)
        improving_areas = []
        declining_areas = []
        if avg_cov >= 75.0:
            improving_areas.append("Curriculum Coverage")
        else:
            declining_areas.append("Curriculum Coverage")

        if avg_val >= 80.0:
            improving_areas.append("Technical Conceptual Accuracy")
        else:
            declining_areas.append("Technical Conceptual Accuracy")

        if avg_tch >= 75.0:
            improving_areas.append("Pedagogical Delivery & Clarity")
        else:
            declining_areas.append("Pedagogical Delivery & Clarity")

        # Skipped topics & incorrect concept topics count
        freq_skipped = [
            f"Topic Skipped in {c.skipped_topics} lecture(s)" for c in cov_summaries if c.skipped_topics > 0
        ]
        freq_incorrect = [
            f"Concept Error in {v.incorrect_concepts} lecture(s)" for v in val_summaries if v.incorrect_concepts > 0
        ]

        summary_text = (
            f"Weekly Performance for Week {week_label}: Analyzed {lecture_count} lecture session(s). "
            f"Average Curriculum Coverage: {avg_cov:.1f}%, Validation Accuracy: {avg_val:.1f}%, "
            f"Teaching Intelligence Score: {avg_tch:.1f}%. "
            f"Generated {total_recs} total recommendation(s) ({crit_count} Critical, {hi_count} High)."
        )

        return RecWeekly(
            faculty_id=faculty_id,
            week_label=week_label,
            lecture_count=lecture_count,
            total_recommendations=total_recs,
            critical_count=crit_count,
            high_count=hi_count,
            medium_count=med_count,
            low_count=lo_count,
            repeated_weaknesses=repeated_weaknesses,
            improving_areas=improving_areas,
            declining_areas=declining_areas,
            frequently_skipped_topics=freq_skipped,
            frequently_incorrect_concepts=freq_incorrect,
            avg_coverage_score=round(avg_cov, 1),
            avg_validation_score=round(avg_val, 1),
            avg_teaching_score=round(avg_tch, 1),
            summary_text=summary_text,
        )
