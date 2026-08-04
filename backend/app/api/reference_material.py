from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
import logging
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reference_material import ReferenceUploadMetadata, ReferenceUploadResponse
from app.services.reference_service import ReferenceService
from app.utils.file_validation import (
    FileTooLargeError,
    InvalidDocumentTypeError,
    MissingMetadataError,
    UnsupportedFileTypeError,
)

router = APIRouter(prefix="/reference", tags=["Reference Uploads"])


@router.post("/upload", response_model=ReferenceUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_reference_material(
    course_name: Annotated[str, Form(...)],
    academic_year: Annotated[str, Form(...)],
    semester: Annotated[str, Form(...)],
    faculty_name: Annotated[str, Form(...)],
    title: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    document_type: Annotated[str, Form(...)],
    description: Annotated[str | None, Form(...)] = None,
) -> ReferenceUploadResponse:
    service = ReferenceService(db)
    metadata = ReferenceUploadMetadata(
        course_name=course_name,
        academic_year=academic_year,
        semester=semester,
        faculty_name=faculty_name,
        title=title,
        document_type=document_type,  # type: ignore[arg-type]
        description=description,
    )

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
        _, response = await service.upload_reference_material(metadata, file)
        db.commit()
        return response
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
        logger = logging.getLogger(__name__)
        logger.exception("Unexpected error during reference material upload")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
