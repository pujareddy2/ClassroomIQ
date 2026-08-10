"""
Data Access Layer for Recommendation Engine.
"""

from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.models.recommendation_engine import (
    RecAnalysis,
    RecEvidence,
    RecItem,
    RecMonthly,
    RecPriority,
    RecSummary,
    RecWeekly,
)


class RecommendationRepository:

    def __init__(self, db: Session):
        self.db = db

    # ── 1. Idempotency & Analysis Lifecycle ───────────────────────────────────

    def get_active_analysis(self, lecture_id: UUID) -> Optional[RecAnalysis]:
        """Find active recommendation analysis for a given lecture_id."""
        return (
            self.db.query(RecAnalysis)
            .options(
                joinedload(RecAnalysis.items).joinedload(RecItem.evidence),
                joinedload(RecAnalysis.items).joinedload(RecItem.priority),
                joinedload(RecAnalysis.summary),
            )
            .filter(
                RecAnalysis.lecture_id == lecture_id,
                RecAnalysis.is_active == True,
            )
            .first()
        )

    def deactivate_previous_analyses(self, lecture_id: UUID, trigger_reason: str = "PREREQUISITE_CHANGED"):
        """Soft-deactivate old active recommendation analyses for a lecture."""
        old_analyses = (
            self.db.query(RecAnalysis)
            .filter(
                RecAnalysis.lecture_id == lecture_id,
                RecAnalysis.is_active == True,
            )
            .all()
        )
        for a in old_analyses:
            a.is_active = False
            a.regeneration_trigger = trigger_reason
        self.db.flush()

    # ── 2. Persistence ────────────────────────────────────────────────────────

    def save_analysis(
        self,
        analysis: RecAnalysis,
        items: List[RecItem],
        evidence_map: Dict[UUID, List[RecEvidence]],
        priorities: List[RecPriority],
        summary: RecSummary,
    ) -> RecAnalysis:
        """Persist full recommendation analysis graph in a single transaction."""
        self.db.add(analysis)
        self.db.flush()

        for item in items:
            item.analysis_id = analysis.id
            self.db.add(item)
            self.db.flush()

            # Attach evidence
            ev_list = evidence_map.get(item.id, [])
            for ev in ev_list:
                ev.item_id = item.id
                self.db.add(ev)

            # Attach priority breakdown
            p_obj = next((p for p in priorities if p.item_id == item.id), None)
            if p_obj:
                p_obj.item_id = item.id
                self.db.add(p_obj)

        summary.analysis_id = analysis.id
        self.db.add(summary)
        self.db.flush()
        return analysis

    # ── 3. Readers ────────────────────────────────────────────────────────────

    def get_items_for_lecture(self, lecture_id: UUID) -> List[RecItem]:
        """Fetch active recommendation items with evidence for a lecture."""
        analysis = self.get_active_analysis(lecture_id)
        if not analysis:
            return []
        return analysis.items

    def get_items_sorted_by_priority(self, lecture_id: UUID) -> List[RecItem]:
        """Fetch active recommendation items sorted descending by priority score."""
        items = self.get_items_for_lecture(lecture_id)
        return sorted(items, key=lambda x: x.priority_score, reverse=True)

    def get_evidence_for_lecture(self, lecture_id: UUID) -> List[RecEvidence]:
        """Fetch all evidence items attached to active recommendations for a lecture."""
        items = self.get_items_for_lecture(lecture_id)
        all_ev = []
        for it in items:
            all_ev.extend(it.evidence)
        return all_ev

    # ── 4. Weekly & Monthly Summaries ─────────────────────────────────────────

    def save_weekly_summary(self, weekly: RecWeekly) -> RecWeekly:
        self.db.add(weekly)
        self.db.flush()
        return weekly

    def get_weekly_summary(self, faculty_id: UUID, week_label: str) -> Optional[RecWeekly]:
        return (
            self.db.query(RecWeekly)
            .filter(
                RecWeekly.faculty_id == faculty_id,
                RecWeekly.week_label == week_label,
                RecWeekly.status == "ACTIVE",
            )
            .first()
        )

    def save_monthly_summary(self, monthly: RecMonthly) -> RecMonthly:
        self.db.add(monthly)
        self.db.flush()
        return monthly

    def get_monthly_summary(self, faculty_id: UUID, month_label: str) -> Optional[RecMonthly]:
        return (
            self.db.query(RecMonthly)
            .filter(
                RecMonthly.faculty_id == faculty_id,
                RecMonthly.month_label == month_label,
                RecMonthly.status == "ACTIVE",
            )
            .first()
        )

    def get_faculty_history(self, faculty_id: UUID, limit: int = 20) -> List[RecAnalysis]:
        """Fetch recent recommendation analyses for a faculty member."""
        return (
            self.db.query(RecAnalysis)
            .options(joinedload(RecAnalysis.summary))
            .filter(RecAnalysis.faculty_id == faculty_id)
            .order_by(desc(RecAnalysis.created_at))
            .limit(limit)
            .all()
        )
