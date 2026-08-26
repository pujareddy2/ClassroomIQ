"""
AssistantService — Grounded AI Assistant service for ClassroomIQ.
Consumes RAGRetrievalService to answer user academic questions using authorized course references.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from app.models.coverage_summary import CoverageSummary
from app.models.explanation_engine import ExplanationSummary
from app.models.recommendation_engine import RecAnalysis
from app.models.teaching_intelligence import TeachingSummary
from app.models.validation_summary import ValidationSummary
from app.models.curriculum import Curriculum
from app.services.rag.rag_retrieval_service import RAGRetrievalService

logger = logging.getLogger(__name__)


class AssistantService:
    """Service orchestrator for RAG-grounded AI Assistant."""

    def __init__(self, db: Session):
        self.db = db
        self.rag_service = RAGRetrievalService(db)

    def answer_question(
        self,
        question: str,
        lecture_id: Optional[UUID] = None,
        course_id: Optional[UUID] = None,
        curriculum_id: Optional[UUID] = None,
        topic_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Answers a user question grounded in indexed academic reference material (RAG).
        Enforces course isolation, no-hallucination fallback, and citation provenance.
        """
        clean_q = question.strip()
        if not clean_q:
            return {
                "answer": "Please enter a valid question.",
                "grounded": False,
                "confidence_score": 0.0,
                "evidence_count": 0,
                "sources": [],
            }

        # Resolve course_id if only curriculum_id or lecture_id is passed
        resolved_course_id = course_id
        if not resolved_course_id and curriculum_id:
            curr = self.db.get(Curriculum, curriculum_id)
            if curr:
                resolved_course_id = curr.course_id

        # 1. Query RAG Retrieval Service
        bundle = self.rag_service.retrieve_evidence(
            query=clean_q,
            course_id=resolved_course_id,
            topic_id=topic_id,
            top_k=5,
        )

        sources = []
        is_grounded = False
        confidence = 0.0
        answer_text = ""

        if bundle and bundle.total_results > 0 and bundle.evidence:
            top_ev = bundle.evidence[0]
            if top_ev.final_score >= 0.15:
                is_grounded = True
                confidence = round(top_ev.final_score * 100, 1)
                
                for ev in bundle.evidence:
                    sources.append({
                        "reference_chunk_id": str(ev.chunk_id),
                        "reference_material_id": str(ev.reference_material_id),
                        "document_title": ev.document_title,
                        "section_title": ev.section_title or "General Section",
                        "page_number": ev.page_number,
                        "excerpt": ev.chunk_text,
                        "relevance_score": round(ev.final_score, 4),
                    })

                sec_label = f" ({top_ev.section_title})" if top_ev.section_title else ""
                answer_text = f"According to course reference '{top_ev.document_title}'{sec_label}: {top_ev.chunk_text[:350]}"
                if len(top_ev.chunk_text) > 350:
                    answer_text += "..."

        # 2. Fallback to Lecture Analysis Summaries if question relates to lecture analytics
        if not is_grounded and lecture_id:
            q_lower = clean_q.lower()
            cov = self.db.query(CoverageSummary).filter(CoverageSummary.lecture_id == lecture_id).first()
            val = self.db.query(ValidationSummary).filter(ValidationSummary.lecture_id == lecture_id).first()
            tch = self.db.query(TeachingSummary).filter(TeachingSummary.lecture_id == lecture_id).first()
            rec = self.db.query(RecAnalysis).filter(RecAnalysis.lecture_id == lecture_id).first()

            if any(k in q_lower for k in ("skip", "coverage", "topic")) and cov:
                answer_text = f"Coverage is {cov.weighted_coverage_percentage:.1f}%. {cov.skipped_topics} topic(s) skipped and {cov.rushed_topics} rushed."
                is_grounded = True
                confidence = 85.0
            elif any(k in q_lower for k in ("validation", "error", "incorrect", "formula")) and val:
                answer_text = f"Validation score is {val.overall_validation_score:.1f}. Found {val.incorrect_concepts} concept issue(s) and {val.formula_issues} formula issue(s)."
                is_grounded = True
                confidence = 85.0
            elif any(k in q_lower for k in ("teach", "quality", "grade")) and tch:
                answer_text = f"Teaching score is {tch.overall_teaching_score:.1f} ({tch.teaching_grade})."
                is_grounded = True
                confidence = 85.0

        # 3. No-Evidence Fallback — Sentinel
        if not is_grounded:
            answer_text = "I couldn't find sufficient supporting material in the indexed course references to answer this reliably."
            confidence = 0.0

        return {
            "answer": answer_text,
            "grounded": is_grounded,
            "confidence_score": confidence,
            "evidence_count": len(sources),
            "sources": sources,
            "context": {
                "course_id": str(resolved_course_id) if resolved_course_id else None,
                "lecture_id": str(lecture_id) if lecture_id else None,
                "curriculum_id": str(curriculum_id) if curriculum_id else None,
                "topic_id": str(topic_id) if topic_id else None,
            },
        }
