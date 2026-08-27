from uuid import UUID
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, TIMESTAMP, text, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("TRUE"), nullable=False)

    # Profile Fields (persisted in DB)
    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("FALSE"), nullable=False)
    institution: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    profile_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    # Explicitly specify foreign_keys to avoid AmbiguousForeignKeysError
    # (faculty.user_id and faculty.created_by both point to users)
    faculty: Mapped[Optional["Faculty"]] = relationship(
        "Faculty",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="[Faculty.user_id]",
    )
    review_decisions: Mapped[List["ReviewDecision"]] = relationship(
        "ReviewDecision",
        back_populates="reviewer",
        foreign_keys="[ReviewDecision.reviewer_id]",
    )
