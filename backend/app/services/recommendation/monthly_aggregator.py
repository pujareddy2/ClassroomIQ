"""
Module 7: Monthly Recommendation Aggregator

Aggregates weekly recommendation summaries across one academic month (e.g., '2026-08')
for a faculty member. Generates monthly improvement reports and trend metrics.
"""

from collections import Counter
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.recommendation_engine import RecMonthly, RecWeekly


class MonthlyAggregator:

    def __init__(self, db: Session):
        self.db = db

    def aggregate_month(
        self, faculty_id: UUID, month_label: str = "2026-08"
    ) -> RecMonthly:
        """Aggregate weekly summaries into a monthly report."""

        # Fetch weekly summaries for this month
        weeklies = (
            self.db.query(RecWeekly)
            .filter(
                RecWeekly.faculty_id == faculty_id,
                RecWeekly.week_label.like(f"{month_label[:4]}%"),
                RecWeekly.status == "ACTIVE",
            )
            .all()
        )

        week_count = len(weeklies)
        if week_count == 0:
            return RecMonthly(
                faculty_id=faculty_id,
                month_label=month_label,
                week_count=0,
                lecture_count=0,
                total_recommendations=0,
                coverage_trend=[],
                validation_trend=[],
                teaching_trend=[],
                interaction_trend=[],
                overall_progress_score=0.0,
                monthly_improvement_report="No active weekly data found for this month.",
                top_recurring_issues=["No data available."],
                most_improved_areas=[],
            )

        lecture_count = sum(w.lecture_count for w in weeklies)
        total_recs = sum(w.total_recommendations for w in weeklies)

        coverage_trend = [w.avg_coverage_score for w in weeklies]
        validation_trend = [w.avg_validation_score for w in weeklies]
        teaching_trend = [w.avg_teaching_score for w in weeklies]

        # Calculate overall progress score
        avg_cov_month = sum(coverage_trend) / len(coverage_trend) if coverage_trend else 0.0
        avg_val_month = sum(validation_trend) / len(validation_trend) if validation_trend else 0.0
        avg_tch_month = sum(teaching_trend) / len(teaching_trend) if teaching_trend else 0.0

        overall_progress = round(
            (avg_cov_month * 0.3) + (avg_val_month * 0.4) + (avg_tch_month * 0.3), 1
        )

        # Collect top recurring issues across weeklies
        all_weaknesses = []
        for w in weeklies:
            if w.repeated_weaknesses:
                all_weaknesses.extend(w.repeated_weaknesses)

        issue_counter = Counter(all_weaknesses)
        top_recurring = [issue for issue, _ in issue_counter.most_common(5)]

        most_improved = []
        if len(coverage_trend) >= 2 and coverage_trend[-1] > coverage_trend[0]:
            most_improved.append("Curriculum Coverage Pacing")
        if len(validation_trend) >= 2 and validation_trend[-1] > validation_trend[0]:
            most_improved.append("Technical Conceptual Accuracy")
        if len(teaching_trend) >= 2 and teaching_trend[-1] > teaching_trend[0]:
            most_improved.append("Interactive Teaching Delivery")

        if not most_improved:
            most_improved = ["Maintained Consistent Teaching Performance"]

        monthly_report = (
            f"Monthly Teaching Progress Report for {month_label}: "
            f"Evaluated {lecture_count} lecture(s) across {week_count} week(s). "
            f"Overall Faculty Progress Score: {overall_progress}/100. "
            f"Monthly Coverage Average: {avg_cov_month:.1f}%, Validation Average: {avg_val_month:.1f}%, "
            f"Teaching Score Average: {avg_tch_month:.1f}%. "
            f"Most Improved Area: {', '.join(most_improved)}."
        )

        return RecMonthly(
            faculty_id=faculty_id,
            month_label=month_label,
            week_count=week_count,
            lecture_count=lecture_count,
            total_recommendations=total_recs,
            coverage_trend=coverage_trend,
            validation_trend=validation_trend,
            teaching_trend=teaching_trend,
            interaction_trend=[round(avg_tch_month * 0.9, 1)],
            overall_progress_score=overall_progress,
            monthly_improvement_report=monthly_report,
            top_recurring_issues=top_recurring,
            most_improved_areas=most_improved,
        )
