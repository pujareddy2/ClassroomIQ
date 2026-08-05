"""
Pagination schemas for ClassroomIQ API.

Used by all list endpoints that return multiple records.
"""

from __future__ import annotations

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    """Query parameters for paginated list requests."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")


class PaginationMeta(BaseModel):
    """Pagination metadata returned with every list response."""

    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResult(BaseModel, Generic[T]):
    """Generic paginated result container."""

    items: List[T]
    pagination: PaginationMeta


def make_pagination_meta(page: int, page_size: int, total_items: int) -> PaginationMeta:
    """Build PaginationMeta from raw counts."""
    import math
    total_pages = max(1, math.ceil(total_items / page_size)) if total_items > 0 else 1
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
