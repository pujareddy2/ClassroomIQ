"""HTTP contracts for the centralized AI analysis execution layer."""

from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisRunRequest(BaseModel):
    lecture_id: UUID
    curriculum_id: UUID
    regenerate: bool = Field(default=False, description="Create a new execution after a completed analysis.")
