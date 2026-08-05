"""
CitationRepository

Database operations for ReferenceCitation.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.explanation_engine import ReferenceCitation


class CitationRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_evidence_item(self, evidence_item_id: UUID) -> Optional[ReferenceCitation]:
        return (
            self.db.query(ReferenceCitation)
            .filter(ReferenceCitation.evidence_item_id == evidence_item_id)
            .first()
        )

    def get_by_reference_material(self, reference_material_id: UUID) -> List[ReferenceCitation]:
        return (
            self.db.query(ReferenceCitation)
            .filter(ReferenceCitation.reference_material_id == reference_material_id)
            .all()
        )

    def save(self, citation: ReferenceCitation) -> ReferenceCitation:
        self.db.add(citation)
        self.db.flush()
        return citation

    def has_citation(self, evidence_item_id: UUID) -> bool:
        return (
            self.db.query(ReferenceCitation)
            .filter(ReferenceCitation.evidence_item_id == evidence_item_id)
            .count()
            > 0
        )
