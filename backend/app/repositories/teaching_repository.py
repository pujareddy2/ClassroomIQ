"""
TeachingRepository — Data access layer for Teaching Intelligence.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.teaching_intelligence import (
    TeachingAnalysis,
    TeachingExample,
    TeachingExplanation,
    TeachingInteraction,
    TeachingScoreWeight,
    TeachingStructure,
    TeachingSummary,
)
from app.repositories.base_repository import BaseRepository


class TeachingRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    # ── Score Weights ─────────────────────────────────────────────────────────

    def get_active_score_weights(self) -> Dict[str, float]:
        """Loads active metric weights from the DB; seeds defaults if table is empty."""
        stmt = select(TeachingScoreWeight).where(TeachingScoreWeight.is_active.is_(True))
        rows = self.db.execute(stmt).scalars().all()
        if not rows:
            defaults = [
                ("Explanation", 30.0),
                ("Examples", 20.0),
                ("Structure", 20.0),
                ("Interaction", 15.0),
                ("Coverage", 10.0),
                ("Validation", 5.0),
            ]
            weights_map = {}
            for metric, weight_val in defaults:
                sw = TeachingScoreWeight(metric_name=metric, weight=weight_val, is_active=True)
                self.db.add(sw)
                weights_map[metric] = weight_val
            self.db.flush()
            return weights_map
        return {r.metric_name: r.weight for r in rows}

    # ── Analysis Lifecycle ───────────────────────────────────────────────────

    def get_active_analysis(self, lecture_id: UUID) -> Optional[TeachingAnalysis]:
        """Fetch the currently active TeachingAnalysis for a lecture session."""
        stmt = select(TeachingAnalysis).where(
            TeachingAnalysis.lecture_id == lecture_id,
            TeachingAnalysis.is_active.is_(True),
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def deactivate_previous_analyses(self, lecture_id: UUID, trigger_reason: str) -> None:
        """Mark older analyses for this lecture as inactive/superseded."""
        stmt = (
            update(TeachingAnalysis)
            .where(
                TeachingAnalysis.lecture_id == lecture_id,
                TeachingAnalysis.is_active.is_(True),
            )
            .values(is_active=False, regeneration_trigger=trigger_reason)
        )
        self.db.execute(stmt)
        self.db.flush()

    # ── Persistence ───────────────────────────────────────────────────────────

    def create_teaching_record(
        self,
        analysis: TeachingAnalysis,
        summary: TeachingSummary,
        explanation: TeachingExplanation,
        examples: List[TeachingExample],
        structure: TeachingStructure,
        interaction: TeachingInteraction,
    ) -> TeachingAnalysis:
        """Persist a complete teaching analysis entity graph in a single transaction."""
        self.db.add(analysis)
        self.db.flush()

        summary.analysis_id = analysis.id
        explanation.analysis_id = analysis.id
        structure.analysis_id = analysis.id
        interaction.analysis_id = analysis.id

        self.db.add(summary)
        self.db.add(explanation)
        self.db.add(structure)
        self.db.add(interaction)

        for ex in examples:
            ex.analysis_id = analysis.id
            self.db.add(ex)

        self.db.flush()
        return analysis

    # ── Readers ───────────────────────────────────────────────────────────────

    def get_teaching_summary(self, lecture_id: UUID) -> Optional[TeachingSummary]:
        active_analysis = self.get_active_analysis(lecture_id)
        if not active_analysis:
            return None
        stmt = select(TeachingSummary).where(TeachingSummary.analysis_id == active_analysis.id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_teaching_explanation(self, lecture_id: UUID) -> Optional[TeachingExplanation]:
        active_analysis = self.get_active_analysis(lecture_id)
        if not active_analysis:
            return None
        stmt = select(TeachingExplanation).where(TeachingExplanation.analysis_id == active_analysis.id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_teaching_examples(self, lecture_id: UUID) -> List[TeachingExample]:
        active_analysis = self.get_active_analysis(lecture_id)
        if not active_analysis:
            return []
        stmt = select(TeachingExample).where(TeachingExample.analysis_id == active_analysis.id)
        return list(self.db.execute(stmt).scalars().all())

    def get_teaching_structure(self, lecture_id: UUID) -> Optional[TeachingStructure]:
        active_analysis = self.get_active_analysis(lecture_id)
        if not active_analysis:
            return None
        stmt = select(TeachingStructure).where(TeachingStructure.analysis_id == active_analysis.id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_teaching_interaction(self, lecture_id: UUID) -> Optional[TeachingInteraction]:
        active_analysis = self.get_active_analysis(lecture_id)
        if not active_analysis:
            return None
        stmt = select(TeachingInteraction).where(TeachingInteraction.analysis_id == active_analysis.id)
        return self.db.execute(stmt).scalar_one_or_none()
