"""
Integration tests for Module 6: Weekly Recommendation Aggregator.
"""

import uuid
from sqlalchemy.orm import Session
from app.db.database import engine
from app.services.recommendation.weekly_aggregator import WeeklyAggregator


def test_weekly_aggregator_empty_faculty():
    with Session(engine) as db:
        fac_id = uuid.uuid4()
        aggregator = WeeklyAggregator(db)
        weekly = aggregator.aggregate_week(fac_id, "2026-W31")

        assert weekly.faculty_id == fac_id
        assert weekly.week_label == "2026-W31"
        assert weekly.lecture_count == 0
        assert weekly.total_recommendations == 0
        assert "No active lecture data" in weekly.summary_text
