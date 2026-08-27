from __future__ import annotations

import logging
import time
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.reference_material import ReferenceUploadMetadata, ReferenceUploadResponse
from app.schemas.response import created, ok
from app.services.reference_service import ReferenceService
from app.utils.file_validation import (
    FileTooLargeError,
    InvalidDocumentTypeError,
    MissingMetadataError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reference", tags=["Reference Material"])


@router.post(
    "/upload",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
    summary="Upload reference material",
    description="Validates, extracts, and persists a course reference document for technical validation.",
)
async def upload_reference_material(
    course_name: Annotated[str, Form(...)],
    academic_year: Annotated[str, Form(...)],
    semester: Annotated[str, Form(...)],
    faculty_name: Annotated[str, Form(...)],
    title: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    document_type: Annotated[str, Form(...)],
    description: Annotated[str | None, Form(...)] = None,
) -> dict:
    service = ReferenceService(db)
    try:
        metadata = ReferenceUploadMetadata(
            course_name=course_name,
            academic_year=academic_year,
            semester=semester,
            faculty_name=faculty_name,
            title=title,
            document_type=document_type,  # type: ignore[arg-type]
            description=description,
        )
        start = time.time()
        ref_material, response = await service.upload_reference_material(metadata, file)
        # Stamp ownership so list queries can scope by created_by
        if ref_material is not None and hasattr(ref_material, 'created_by'):
            ref_material.created_by = current_user.id
        db.commit()
        return created(data=response.model_dump(), message="Reference material uploaded.", start_ts=start)
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
        logger.exception("Unexpected error during reference material upload")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/list",
    summary="List my reference materials",
    description="Returns reference materials uploaded by the authenticated faculty member.",
)
def list_reference_materials(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    course_id: UUID | None = Query(default=None),
) -> dict:
    from app.models.reference_material import ReferenceMaterial
    query = db.query(ReferenceMaterial).filter(
        ReferenceMaterial.deleted_at.is_(None),
        ReferenceMaterial.created_by == current_user.id,
    )
    if course_id:
        query = query.filter(ReferenceMaterial.course_id == course_id)
    items = query.all()
    results = [
        {
            "id": str(m.id),
            "course_id": str(m.course_id),
            "title": m.title,
            "document_type": m.document_type,
            "file_name": m.file_name,
            "file_size": m.file_size,
            "processing_status": m.processing_status,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in items
    ]
    return ok(data=results, message="Reference materials retrieved.")


@router.delete(
    "/{reference_id}",
    summary="Delete reference material",
    description="Soft deletes a reference material.",
)
def delete_reference_material(
    reference_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    from app.repositories.reference_repository import ReferenceRepository
    from app.models.reference_material import ReferenceMaterial
    repo = ReferenceRepository(db)
    ref = repo.soft_delete_reference(reference_id)
    if ref is None:
        item = db.get(ReferenceMaterial, reference_id)
        if item:
            item.deleted_at = datetime.now(timezone.utc)
            db.commit()
            return ok(data={"id": str(reference_id)}, message="Reference material deleted.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference material not found.")
    db.commit()
    return ok(data={"id": str(reference_id)}, message="Reference material deleted.")
