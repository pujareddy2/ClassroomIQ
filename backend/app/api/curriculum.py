"""
REST API router for Curriculum Intelligence Module.
Versioned under /api/v1/curriculum (prefix applied at registration in main.py).

Routes:
  POST   /curriculum/upload              — Upload curriculum document
  GET    /curriculum                     — List all curricula (paginated)
  GET    /curriculum/{id}                — Full hierarchy (units, chapters, topics, outcomes)
  GET    /curriculum/{id}/tree           — Tree structure only
  GET    /curriculum/{id}/segments       — AI pipeline segments (RAG, Coverage, Mapping)
  GET    /curriculum/{id}/statistics     — Node counts, tree depth, structural validation
  GET    /curriculum/{id}/node/{node_id} — Single node detail
  DELETE /curriculum/{id}                — Soft delete
"""

from __future__ import annotations

import logging
import time
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.curriculum_repository import CurriculumRepository
from app.schemas.curriculum import (
    CurriculumDeleteResponse,
    CurriculumListItem,
    CurriculumUploadMetadata,
    CurriculumUploadResponse,
)
from app.schemas.response import created, ok, paginated
from app.services.curriculum_hierarchy.exceptions import (
    CurriculumNotFoundError,
    EmptyCurriculumError,
    InvalidHierarchyError,
)
from app.services.curriculum_hierarchy.hierarchy_models import (
    CurriculumHierarchyResponse,
    CurriculumSegmentsResponse,
    CurriculumStatisticsResponse,
    CurriculumTreeResponse,
    NodeDetailResponse,
)
from app.services.curriculum_hierarchy.hierarchy_service import CurriculumHierarchyService
from app.services.curriculum_service import CurriculumService
from app.utils.file_validation import (
    FileTooLargeError,
    InvalidDocumentTypeError,
    MissingMetadataError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/curriculum", tags=["Curriculum Intelligence"])


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload a curriculum document",
    description=(
        "Accepts a PDF, DOCX, or TXT curriculum/syllabus file. "
        "Extracts text, parses the unit/chapter/topic hierarchy, persists to PostgreSQL, "
        "and returns the full structured curriculum tree."
    ),
)
async def upload_curriculum(
    course_name: Annotated[str, Form(...)],
    academic_year: Annotated[str, Form(...)],
    semester: Annotated[str, Form(...)],
    faculty_name: Annotated[str, Form(...)],
    title: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    document_type: Annotated[str, Form(...)] = "SYLLABUS",
    description: Annotated[str | None, Form(...)] = None,
) -> dict:
    start = time.time()
    service = CurriculumService(db)
    try:
        metadata = CurriculumUploadMetadata(
            course_name=course_name,
            academic_year=academic_year,
            semester=semester,
            faculty_name=faculty_name,
            title=title,
            document_type=document_type,
            description=description,
        )
        curriculum, response = await service.upload_curriculum(metadata, file)
        # Stamp ownership on the curriculum record
        if curriculum is not None and hasattr(curriculum, 'created_by'):
            curriculum.created_by = current_user.id
        db.commit()
        return created(
            data=response.model_dump(),
            message="Curriculum uploaded and parsed successfully.",
            start_ts=start,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()) from exc
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)) from exc
    except FileTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)) from exc
    except InvalidDocumentTypeError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except MissingMetadataError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error during curriculum upload")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List my curricula",
    description="Returns a paginated list of curricula belonging to the authenticated faculty.",
)
def list_curricula(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    course_id: Optional[UUID] = Query(default=None, description="Filter by course UUID"),
) -> dict:
    start = time.time()
    repo = CurriculumRepository(db)
    # Always scope to the current user's curricula (created_by)
    # Use created_by UUID for ownership filtering
    items, pagination_meta = repo.list_curricula_by_owner(
        owner_id=current_user.id,
        page=page,
        page_size=page_size,
        course_id=course_id,
    )
    data = [CurriculumListItem.model_validate(c).model_dump() for c in items]
    return paginated(
        items=data,
        pagination=pagination_meta,
        message=f"{pagination_meta.total_items} curricula found.",
        start_ts=start,
    )


@router.get(
    "/{curriculum_id}",
    status_code=status.HTTP_200_OK,
    summary="Get full curriculum hierarchy",
    description="Returns the complete structured hierarchy: units, chapters, topics, and learning outcomes.",
)
def get_curriculum_hierarchy(
    curriculum_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start = time.time()
    service = CurriculumHierarchyService(db)
    try:
        result = service.get_full_hierarchy(curriculum_id)
        return ok(data=result.model_dump(), message="Curriculum hierarchy retrieved.", start_ts=start)
    except CurriculumNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EmptyCurriculumError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching curriculum hierarchy")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{curriculum_id}/tree",
    status_code=status.HTTP_200_OK,
    summary="Get curriculum tree structure",
    description="Returns the reconstructed tree hierarchy using parent_topic_id relationships.",
)
def get_curriculum_tree(
    curriculum_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start = time.time()
    service = CurriculumHierarchyService(db)
    try:
        result = service.get_tree_only(curriculum_id)
        return ok(data=result.model_dump(), message="Curriculum tree retrieved.", start_ts=start)
    except CurriculumNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EmptyCurriculumError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching curriculum tree")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{curriculum_id}/segments",
    status_code=status.HTTP_200_OK,
    summary="Get curriculum segments for AI pipelines",
    description="Returns logical curriculum segments used by Transcript Mapper, Coverage Engine, and RAG pipeline.",
)
def get_curriculum_segments(
    curriculum_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start = time.time()
    service = CurriculumHierarchyService(db)
    try:
        result = service.get_segments(curriculum_id)
        return ok(data=result.model_dump(), message="Curriculum segments retrieved.", start_ts=start)
    except CurriculumNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EmptyCurriculumError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching curriculum segments")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{curriculum_id}/statistics",
    status_code=status.HTTP_200_OK,
    summary="Get curriculum structural statistics",
    description="Returns node counts by type, tree depth, and structural validation status.",
)
def get_curriculum_statistics(
    curriculum_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start = time.time()
    service = CurriculumHierarchyService(db)
    try:
        result = service.get_statistics(curriculum_id)
        return ok(data=result.model_dump(), message="Curriculum statistics retrieved.", start_ts=start)
    except CurriculumNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EmptyCurriculumError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching curriculum statistics")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{curriculum_id}/node/{node_id}",
    status_code=status.HTTP_200_OK,
    summary="Get single node detail",
    description="Returns complete metadata, hierarchy path, parent, children, and siblings for a specific node.",
)
def get_node_detail(
    curriculum_id: UUID,
    node_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start = time.time()
    service = CurriculumHierarchyService(db)
    try:
        result = service.get_node_detail(curriculum_id, node_id)
        return ok(data=result.model_dump(), message="Node detail retrieved.", start_ts=start)
    except CurriculumNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching node detail")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.delete(
    "/{curriculum_id}",
    status_code=status.HTTP_200_OK,
    summary="Soft-delete a curriculum",
    description=(
        "Marks the curriculum as DELETED (sets status=DELETED, deleted_at=now()). "
        "The record is retained in PostgreSQL for audit and FK integrity. "
        "The curriculum will no longer appear in list queries."
    ),
)
def delete_curriculum(
    curriculum_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start = time.time()
    repo = CurriculumRepository(db)
    curriculum = repo.soft_delete_curriculum(curriculum_id)
    if curriculum is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Curriculum '{curriculum_id}' not found.",
        )
    db.commit()
    return ok(
        data=CurriculumDeleteResponse(
            curriculum_id=curriculum_id,
            status="DELETED",
            message="Curriculum soft-deleted successfully.",
        ).model_dump(),
        message="Curriculum deleted.",
        start_ts=start,
    )
