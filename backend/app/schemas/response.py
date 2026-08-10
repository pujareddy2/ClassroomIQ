"""
Standard API response envelope for ClassroomIQ v1 API.

Every endpoint must return one of:
  - ApiResponse[T]      for single-resource or action responses
  - PaginatedResponse[T] for list responses
  - ApiErrorResponse    is raised automatically by exception handlers

Usage in a router:
    from app.schemas.response import ok, created, paginated
    return ok(data=my_schema, message="Curriculum retrieved.")
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Generic, List, Optional, TypeVar

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.schemas.pagination import PaginationMeta

T = TypeVar("T")

API_VERSION = "v1"


# ── Metadata ──────────────────────────────────────────────────────────────────

class ResponseMetadata(BaseModel):
    timestamp: str
    execution_time: Optional[float] = None
    api_version: str = API_VERSION
    request_id: str


# ── Success Envelopes ─────────────────────────────────────────────────────────

class ApiResponse(BaseModel, Generic[T]):
    """Standard single-resource response envelope."""

    status: str = "SUCCESS"
    message: str = ""
    data: T
    metadata: ResponseMetadata


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list response envelope."""

    status: str = "SUCCESS"
    message: str = ""
    data: List[T]
    pagination: PaginationMeta
    metadata: ResponseMetadata


# ── Error Envelope ────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ApiErrorResponse(BaseModel):
    status: str = "ERROR"
    message: str
    error: dict[str, Any] = Field(default_factory=dict)
    metadata: ResponseMetadata


# ── Builder Helpers ───────────────────────────────────────────────────────────

def _meta(start_ts: Optional[float] = None) -> ResponseMetadata:
    now = time.time()
    return ResponseMetadata(
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        execution_time=round((now - start_ts) * 1000, 2) if start_ts else None,
        api_version=API_VERSION,
        request_id=str(uuid.uuid4()),
    )


def ok(data: Any, message: str = "", start_ts: Optional[float] = None) -> dict:
    """Build a 200 SUCCESS envelope dict."""
    return ApiResponse(
        status="SUCCESS",
        message=message,
        data=data,
        metadata=_meta(start_ts),
    ).model_dump(mode="json")


def created(data: Any, message: str = "", start_ts: Optional[float] = None) -> dict:
    """Build a 201 CREATED envelope dict."""
    return ApiResponse(
        status="SUCCESS",
        message=message,
        data=data,
        metadata=_meta(start_ts),
    ).model_dump(mode="json")


def paginated(
    items: List[Any],
    pagination: PaginationMeta,
    message: str = "",
    start_ts: Optional[float] = None,
) -> dict:
    """Build a paginated list envelope dict."""
    return PaginatedResponse(
        status="SUCCESS",
        message=message,
        data=items,
        pagination=pagination,
        metadata=_meta(start_ts),
    ).model_dump(mode="json")


def error_response(message: str, code: str, details: List[Any] = None, status_code: int = 400) -> JSONResponse:
    """Build a standard error JSONResponse."""
    body = ApiErrorResponse(
        status="ERROR",
        message=message,
        error={"code": code, "details": details or []},
        metadata=_meta(),
    ).model_dump(mode="json")
    return JSONResponse(status_code=status_code, content=body)
