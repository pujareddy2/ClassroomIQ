from uuid import UUID
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, TIMESTAMP, text, UniqueConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class TopicReference(Base):
    __tablename__ = "topic_references"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    topic_id: Mapped[UUID] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    reference_material_id: Mapped[UUID] = mapped_column(ForeignKey("reference_materials.id", ondelete="CASCADE"), nullable=False)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("topic_id", "reference_material_id", name="uq_topic_reference"),
    )

    # Relationships
    topic: Mapped["Topic"] = relationship("Topic", back_populates="topic_references")
    reference_material: Mapped["ReferenceMaterial"] = relationship("ReferenceMaterial", back_populates="topic_references")
