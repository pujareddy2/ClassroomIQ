"""
REST API router for RAG-Grounded ClassroomIQ AI Assistant Engine.
"""

from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.response import ok
from app.services.assistant.assistant_service import AssistantService

router = APIRouter(prefix="/assistant", tags=["ClassroomIQ Assistant"])


class AssistantQuestionPayload(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    lecture_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    curriculum_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    conversation_id: Optional[str] = None


@router.post("/ask", status_code=status.HTTP_200_OK, summary="Answer an academic question using RAG evidence")
@router.post("/chat", status_code=status.HTTP_200_OK, summary="Chat with ClassroomIQ assistant grounded in RAG evidence")
def ask_assistant(
    payload: AssistantQuestionPayload,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """
    POST /assistant/ask & POST /assistant/chat
    Answers academic questions grounded in RAG reference evidence.
    """
    service = AssistantService(db)
    result = service.answer_question(
        question=payload.question,
        lecture_id=payload.lecture_id,
        course_id=payload.course_id,
        curriculum_id=payload.curriculum_id,
        topic_id=payload.topic_id,
    )
    if payload.conversation_id:
        result["conversation_id"] = payload.conversation_id
        
    return ok(data=result, message="Grounded assistant response generated.")
