"""Lecture-aware assistant that answers only from persisted ClassroomIQ data."""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.coverage_summary import CoverageSummary
from app.models.explanation_engine import ExplanationSummary
from app.models.recommendation_engine import RecAnalysis
from app.models.teaching_intelligence import TeachingSummary
from app.models.validation_summary import ValidationSummary
from app.schemas.response import ok
router = APIRouter(prefix="/assistant", tags=["ClassroomIQ Assistant"])
class AssistantQuestion(BaseModel): lecture_id: UUID; question: str = Field(min_length=2, max_length=500)
@router.post("/ask", summary="Answer a question from persisted lecture analysis")
def ask_assistant(payload: AssistantQuestion, db: Annotated[Session, Depends(get_db)]) -> dict:
    q = payload.question.lower(); coverage = db.execute(select(CoverageSummary).where(CoverageSummary.lecture_id == payload.lecture_id).order_by(CoverageSummary.created_at.desc())).scalars().first(); validation = db.execute(select(ValidationSummary).where(ValidationSummary.lecture_id == payload.lecture_id).order_by(ValidationSummary.created_at.desc())).scalars().first(); teaching = db.execute(select(TeachingSummary).where(TeachingSummary.lecture_id == payload.lecture_id).order_by(TeachingSummary.created_at.desc())).scalars().first(); recommendations = db.execute(select(RecAnalysis).where(RecAnalysis.lecture_id == payload.lecture_id, RecAnalysis.is_active.is_(True))).scalars().first(); explanation = db.execute(select(ExplanationSummary).where(ExplanationSummary.lecture_id == payload.lecture_id).order_by(ExplanationSummary.created_at.desc())).scalars().first()
    if not any((coverage, validation, teaching, recommendations, explanation)): answer = "Analysis has not been generated for this lecture yet. Run Complete AI Analysis first."
    elif any(t in q for t in ("skip", "coverage", "topic")) and coverage: answer = f"Coverage is {coverage.weighted_coverage:.1f}%. The analysis records {coverage.skipped_topics} skipped and {coverage.rushed_topics} rushed topic(s)."
    elif any(t in q for t in ("validation", "incorrect", "formula", "error")) and validation: answer = f"Validation score is {validation.overall_validation_score:.1f}. It found {validation.incorrect_concepts} incorrect concepts, {validation.formula_issues} formula issues, and {validation.code_issues} code issues."
    elif any(t in q for t in ("teach", "weak", "strength", "improve")) and teaching: answer = f"Teaching score is {teaching.overall_teaching_score:.1f} ({teaching.teaching_grade}). Strengths: {', '.join(teaching.strengths or []) or 'none recorded'}. Weaknesses: {', '.join(teaching.weaknesses or []) or 'none recorded'}."
    elif any(t in q for t in ("recommend", "suggest", "action")) and recommendations: answer = f"There are {recommendations.total_recommendations} active recommendations: {recommendations.critical_count} critical and {recommendations.high_count} high priority."
    elif explanation: answer = "Explainability evidence is available. Open Explainable AI to inspect linked transcript snippets, citations, confidence, and reasoning."
    else: answer = "The requested analysis is not available yet. Run Complete AI Analysis, then try again."
    return ok(data={"answer": answer, "lecture_id": str(payload.lecture_id)}, message="Lecture-aware assistant response generated.")
