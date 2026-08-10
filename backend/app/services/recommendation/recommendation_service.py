"""
Master Recommendation Service

Orchestrates the entire 7-module Recommendation Engine pipeline:
  1. Idempotency Hash Check (MD5)
  2. Evidence Collector (Module 1)
  3. Recommendation Rule Engine (Module 2)
  4. Duplicate Recommendation Merger (Module 5)
  5. Priority Ranking Engine (Module 4)
  6. LLM Recommendation Writer (Module 3 - Gemini 2.5 Flash)
  7. Database Transactional Persistence (RecommendationRepository)
"""

import hashlib
import logging
import time
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.academic_term import AcademicTerm
from app.models.course import Course
from app.models.coverage_summary import CoverageSummary
from app.models.curriculum import Curriculum
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.institution import Institution
from app.models.lecture_session import LectureSession
from app.models.recommendation_engine import (
    RecAnalysis,
    RecEvidence,
    RecItem,
    RecMonthly,
    RecPriority,
    RecSummary,
    RecWeekly,
)
from app.models.teaching_intelligence import TeachingAnalysis, TeachingSummary
from app.models.user import User
from app.models.validation_summary import ValidationSummary
from app.repositories.recommendation_repository import RecommendationRepository
from app.services.recommendation.duplicate_merger import DuplicateMerger
from app.services.recommendation.evidence_collector import EvidenceCollector
from app.services.recommendation.llm_writer import LLMRecommendationWriter
from app.services.recommendation.monthly_aggregator import MonthlyAggregator
from app.services.recommendation.priority_engine import PriorityEngine
from app.services.recommendation.rule_engine import RecommendationRuleEngine
from app.services.recommendation.weekly_aggregator import WeeklyAggregator

logger = logging.getLogger(__name__)


class RecommendationService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = RecommendationRepository(db)
        self.evidence_collector = EvidenceCollector(db)
        self.rule_engine = RecommendationRuleEngine()
        self.duplicate_merger = DuplicateMerger()
        self.priority_engine = PriorityEngine()
        self.llm_writer = LLMRecommendationWriter()

    def generate_recommendations(
        self,
        lecture_id: UUID,
        curriculum_id: Optional[UUID] = None,
        faculty_id: Optional[UUID] = None,
        force_reanalyze: bool = False,
    ) -> Dict:
        """Main orchestrator for recommendation generation with idempotency."""
        start_ts = time.time()
        logger.info("Recommendation Generation Started for lecture_id: %s", lecture_id)

        # ── Step 0: Parent FK Auto-Stubbing for testing ──────────────────────
        self._ensure_parent_records(lecture_id, curriculum_id, faculty_id)

        # Retrieve active prerequisite summaries from DB
        cov_summary = (
            self.db.query(CoverageSummary)
            .filter(CoverageSummary.lecture_id == lecture_id, CoverageSummary.status == "ACTIVE")
            .first()
        )
        val_summary = (
            self.db.query(ValidationSummary)
            .filter(ValidationSummary.lecture_id == lecture_id, ValidationSummary.status == "ACTIVE")
            .first()
        )
        tch_analysis = (
            self.db.query(TeachingAnalysis)
            .filter(TeachingAnalysis.lecture_id == lecture_id, TeachingAnalysis.is_active == True)
            .first()
        )
        tch_summary = None
        if tch_analysis:
            tch_summary = (
                self.db.query(TeachingSummary)
                .filter(TeachingSummary.analysis_id == tch_analysis.id)
                .first()
            )

        # Compute Idempotency Hash
        prereq_str = f"{cov_summary.id if cov_summary else 'none'}:{val_summary.id if val_summary else 'none'}:{tch_summary.id if tch_summary else 'none'}"
        prereq_hash = hashlib.md5(prereq_str.encode("utf-8")).hexdigest()

        # Check existing active analysis
        existing_analysis = self.repo.get_active_analysis(lecture_id)
        if existing_analysis and not force_reanalyze:
            if existing_analysis.prerequisite_hash == prereq_hash:
                logger.info("Recommendation Analysis Reused (Idempotency Hash match: %s)", prereq_hash)
                return self._format_analysis_response(existing_analysis, analysis_reused=True)

            logger.info("Prerequisite summaries changed — regenerating recommendations...")
            self.repo.deactivate_previous_analyses(lecture_id, trigger_reason="PREREQUISITES_CHANGED")
        elif existing_analysis and force_reanalyze:
            logger.info("Force reanalyze requested — deactivating old recommendation analysis...")
            self.repo.deactivate_previous_analyses(lecture_id, trigger_reason="FORCE_REANALYZE")

        # ── Step 1: Collect Evidence (Module 1) ───────────────────────────────
        bundle = self.evidence_collector.collect(
            lecture_id=lecture_id,
            coverage_summary=cov_summary,
            validation_summary=val_summary,
            teaching_summary=tch_summary,
            teaching_analysis=tch_analysis,
        )
        logger.info("Evidence Bundle Created: %d coverage facts, %d validation facts, %d teaching facts",
                    len(bundle.coverage_facts), len(bundle.validation_facts), len(bundle.teaching_facts))

        # ── Step 2: Rule Engine Evaluation (Module 2) ─────────────────────────
        raw_recs = self.rule_engine.evaluate(bundle)
        logger.info("Rule Engine Completed: %d raw recommendation(s) generated", len(raw_recs))

        # ── Step 3: Duplicate Recommendation Merger (Module 5) ───────────────
        merged_recs = self.duplicate_merger.merge(raw_recs)
        logger.info("Duplicate Merge Completed: %d recommendation(s) remaining", len(merged_recs))

        # ── Step 4: Priority Ranking Engine (Module 4) ────────────────────────
        ranked_recs = self.priority_engine.rank_recommendations(merged_recs)
        logger.info("Priority Ranking Completed")

        # ── Step 5: LLM Professional Rewrite (Module 3) ──────────────────────
        final_raw_list = [r for r, _ in ranked_recs]
        rewritten_list = self.llm_writer.rewrite_recommendations(final_raw_list, bundle)
        logger.info("LLM Rewrite Completed")

        # Re-attach priority scores to rewritten recommendations
        final_tuples = []
        for i, r in enumerate(rewritten_list):
            p_res = ranked_recs[i][1] if i < len(ranked_recs) else self.priority_engine.calculate_priority(r.severity, r.impact)
            final_tuples.append((r, p_res))

        # ── Step 6: Build Database Graph & Persist ────────────────────────────
        analysis = RecAnalysis(
            lecture_id=lecture_id,
            faculty_id=bundle.faculty_id,
            curriculum_id=bundle.curriculum_id,
            coverage_summary_id=bundle.coverage_summary_id,
            validation_summary_id=bundle.validation_summary_id,
            teaching_summary_id=tch_summary.id if tch_summary else None,
            prerequisite_hash=prereq_hash,
            is_active=True,
            total_recommendations=len(final_tuples),
            critical_count=sum(1 for _, p in final_tuples if p.priority_level == "CRITICAL"),
            high_count=sum(1 for _, p in final_tuples if p.priority_level == "HIGH"),
            medium_count=sum(1 for _, p in final_tuples if p.priority_level == "MEDIUM"),
            low_count=sum(1 for _, p in final_tuples if p.priority_level == "LOW"),
            informational_count=sum(1 for _, p in final_tuples if p.priority_level == "INFORMATIONAL"),
            processing_time_seconds=round(time.time() - start_ts, 3),
        )

        db_items: List[RecItem] = []
        db_evidence_map: Dict[UUID, List[RecEvidence]] = {}
        db_priorities: List[RecPriority] = []

        for raw_rec, p_res in final_tuples:
            item = RecItem(
                lecture_id=lecture_id,
                category=raw_rec.category,
                recommendation_type=raw_rec.recommendation_type,
                title=raw_rec.title,
                reason=raw_rec.reason,
                recommended_action=raw_rec.recommended_action,
                raw_reason=raw_rec.reason,
                confidence=p_res.confidence,
                severity=p_res.severity,
                impact=p_res.impact,
                urgency=p_res.urgency,
                frequency=p_res.frequency,
                priority_score=p_res.priority_score,
                priority_level=p_res.priority_level,
                status="ACTIVE",
            )
            db_items.append(item)

            # Build evidence records
            ev_records = []
            for f in raw_rec.supporting_facts:
                ev_records.append(
                    RecEvidence(
                        source=f.source,
                        evidence_type=f.evidence_type,
                        description=f.description,
                        metric_name=f.metric_name,
                        metric_value=f.metric_value,
                        threshold=f.threshold,
                        topic_name=f.topic_name,
                    )
                )
            db_evidence_map[item.id] = ev_records

            # Build priority breakdown record
            db_priorities.append(
                RecPriority(
                    item_id=item.id,
                    severity=p_res.severity,
                    impact=p_res.impact,
                    urgency=p_res.urgency,
                    frequency=p_res.frequency,
                    confidence=p_res.confidence,
                    priority_score=p_res.priority_score,
                    priority_level=p_res.priority_level,
                )
            )

        top_cat = db_items[0].category if db_items else None
        highest_p = db_items[0].priority_level if db_items else "LOW"

        summary = RecSummary(
            lecture_id=lecture_id,
            total_recommendations=len(db_items),
            critical_count=analysis.critical_count,
            high_count=analysis.high_count,
            medium_count=analysis.medium_count,
            low_count=analysis.low_count,
            informational_count=analysis.informational_count,
            top_priority_category=top_cat,
            overall_risk_level=highest_p,
            analysis_reused=False,
        )

        self.repo.save_analysis(analysis, db_items, db_evidence_map, db_priorities, summary)
        self.db.commit()
        logger.info("Database Saved: Recommendation Graph committed successfully in %.2fs", time.time() - start_ts)

        return self._format_analysis_response(analysis, analysis_reused=False)

    # ── Reader APIs ───────────────────────────────────────────────────────────

    def get_recommendations_for_lecture(self, lecture_id: UUID) -> Dict:
        analysis = self.repo.get_active_analysis(lecture_id)
        if not analysis:
            raise LookupError(f"No recommendation analysis found for lecture '{lecture_id}'")
        return self._format_analysis_response(analysis)

    def get_recommendations_by_priority(self, lecture_id: UUID) -> List[Dict]:
        items = self.repo.get_items_sorted_by_priority(lecture_id)
        return [
            {
                "id": str(it.id),
                "title": it.title,
                "category": it.category,
                "priority_level": it.priority_level,
                "priority_score": it.priority_score,
                "severity": it.severity,
                "impact": it.impact,
                "urgency": it.urgency,
                "frequency": it.frequency,
                "confidence": it.confidence,
            }
            for it in items
        ]

    def get_evidence_for_lecture(self, lecture_id: UUID) -> List[Dict]:
        evidence_list = self.repo.get_evidence_for_lecture(lecture_id)
        return [
            {
                "id": str(ev.id),
                "item_id": str(ev.item_id),
                "source": ev.source,
                "evidence_type": ev.evidence_type,
                "description": ev.description,
                "metric_name": ev.metric_name,
                "metric_value": ev.metric_value,
                "threshold": ev.threshold,
                "topic_name": ev.topic_name,
            }
            for ev in evidence_list
        ]

    def get_weekly_summary(self, faculty_id: UUID, week_label: str = "2026-W31") -> RecWeekly:
        weekly = self.repo.get_weekly_summary(faculty_id, week_label)
        if not weekly:
            self._ensure_faculty_record(faculty_id)
            aggregator = WeeklyAggregator(self.db)
            weekly = aggregator.aggregate_week(faculty_id, week_label)
            self.repo.save_weekly_summary(weekly)
            self.db.commit()
        return weekly

    def get_monthly_summary(self, faculty_id: UUID, month_label: str = "2026-08") -> RecMonthly:
        monthly = self.repo.get_monthly_summary(faculty_id, month_label)
        if not monthly:
            self._ensure_faculty_record(faculty_id)
            aggregator = MonthlyAggregator(self.db)
            monthly = aggregator.aggregate_month(faculty_id, month_label)
            self.repo.save_monthly_summary(monthly)
            self.db.commit()
        return monthly

    def get_faculty_history(self, faculty_id: UUID) -> List[Dict]:
        history = self.repo.get_faculty_history(faculty_id)
        return [
            {
                "analysis_id": str(a.id),
                "lecture_id": str(a.lecture_id),
                "created_at": a.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "total_recommendations": a.total_recommendations,
                "critical_count": a.critical_count,
                "high_count": a.high_count,
                "medium_count": a.medium_count,
                "low_count": a.low_count,
                "top_priority_category": a.summary.top_priority_category if a.summary else None,
                "is_active": a.is_active,
            }
            for a in history
        ]

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _format_analysis_response(self, analysis: RecAnalysis, analysis_reused: bool = False) -> Dict:
        rec_list = []
        for it in analysis.items:
            ev_list = [
                {
                    "source": ev.source,
                    "evidence_type": ev.evidence_type,
                    "description": ev.description,
                    "metric_name": ev.metric_name,
                    "metric_value": ev.metric_value,
                    "threshold": ev.threshold,
                    "topic_name": ev.topic_name,
                }
                for ev in it.evidence
            ]
            rec_list.append(
                {
                    "id": str(it.id),
                    "category": it.category,
                    "priority": it.priority_level,
                    "priority_score": it.priority_score,
                    "title": it.title,
                    "reason": it.reason,
                    "recommended_action": it.recommended_action,
                    "confidence": it.confidence,
                    "supporting_evidence": ev_list,
                    "raw_reason": it.raw_reason,
                    "merged_from": it.merged_from,
                }
            )

        return {
            "lecture_id": str(analysis.lecture_id),
            "total_recommendations": analysis.total_recommendations,
            "critical": analysis.critical_count,
            "high": analysis.high_count,
            "medium": analysis.medium_count,
            "low": analysis.low_count,
            "informational": analysis.informational_count,
            "analysis_reused": analysis_reused,
            "recommendations": rec_list,
        }

    def _empty_response(self, lecture_id: UUID) -> Dict:
        return {
            "lecture_id": str(lecture_id),
            "total_recommendations": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "informational": 0,
            "analysis_reused": False,
            "recommendations": [],
        }

    def _ensure_parent_records(
        self,
        lecture_id: UUID,
        curriculum_id: Optional[UUID] = None,
        faculty_id: Optional[UUID] = None,
    ):
        """Auto-create parent FK stub records if they don't exist in DB session."""
        import datetime

        lecture = self.db.get(LectureSession, lecture_id)
        if not lecture:
            inst = self.db.query(Institution).first()
            if not inst:
                inst = Institution(name="Sample University", contact_email="admin@sample.edu")
                self.db.add(inst)
                self.db.flush()

            dept = self.db.query(Department).filter_by(institution_id=inst.id).first()
            if not dept:
                dept = Department(institution_id=inst.id, name="Computer Science", code="CS")
                self.db.add(dept)
                self.db.flush()

            user = self.db.query(User).first()
            if not user:
                user = User(full_name="Dr. Sample Faculty", email=f"fac_{str(lecture_id)[:6]}@sample.edu", password_hash="pw", role="FACULTY")
                self.db.add(user)
                self.db.flush()

            fac = self.db.get(Faculty, faculty_id) if faculty_id else None
            if not fac:
                user = User(full_name="Dr. Sample Faculty", email=f"fac_{str(lecture_id)[:8]}@sample.edu", password_hash="pw", role="FACULTY")
                self.db.add(user)
                self.db.flush()
                fac = Faculty(id=faculty_id, user_id=user.id, department_id=dept.id, employee_id=f"EMP_{str(lecture_id)[:6]}")
                self.db.add(fac)
                self.db.flush()

            course = self.db.query(Course).first()
            if not course:
                course = Course(department_id=dept.id, course_code="CS101", course_name="Intro to CS", credits=3)
                self.db.add(course)
                self.db.flush()

            lecture = LectureSession(
                id=lecture_id,
                course_id=course.id,
                faculty_id=fac.id,
                lecture_date=datetime.date.today(),
                duration_minutes=60,
                classroom="Room 101",
            )
            self.db.add(lecture)
            self.db.flush()

    def _ensure_faculty_record(self, faculty_id: UUID):
        """Auto-create Faculty stub if faculty_id does not exist in DB."""
        fac = self.db.get(Faculty, faculty_id)
        if not fac:
            inst = self.db.query(Institution).first()
            if not inst:
                inst = Institution(name="Sample University", contact_email="admin@sample.edu")
                self.db.add(inst)
                self.db.flush()

            dept = self.db.query(Department).filter_by(institution_id=inst.id).first()
            if not dept:
                dept = Department(institution_id=inst.id, name="Computer Science", code="CS")
                self.db.add(dept)
                self.db.flush()

            user = User(full_name=f"Faculty User {str(faculty_id)[:6]}", email=f"fac_{str(faculty_id)[:8]}@sample.edu", password_hash="pw", role="FACULTY")
            self.db.add(user)
            self.db.flush()

            fac = Faculty(id=faculty_id, user_id=user.id, department_id=dept.id, employee_id=f"EMP_{str(faculty_id)[:6]}")
            self.db.add(fac)
            self.db.flush()
