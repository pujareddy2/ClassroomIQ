"""
Integration tests for Module 7: Monthly Recommendation Aggregator.
"""

import uuid
from sqlalchemy.orm import Session
from app.db.database import engine
from app.services.recommendation.monthly_aggregator import MonthlyAggregator


def test_monthly_aggregator_empty_faculty():
    with Session(engine) as db:
        fac_id = uuid.uuid4()
        aggregator = MonthlyAggregator(db)
        monthly = aggregator.aggregate_month(fac_id, "2026-08")

        assert monthly.faculty_id == fac_id
        assert monthly.month_label == "2026-08"
        assert monthly.week_count == 0
        assert monthly.lecture_count == 0
        assert "No active weekly data" in monthly.monthly_improvement_report
