"""
Unit tests for ReasoningService.
"""

from uuid import uuid4
import pytest
from app.services.xai.reasoning_service import ReasoningService
from app.services.xai.evidence_collector import EvidenceCandidate


def test_reasoning_dag_structure():
    service = ReasoningService()

    candidate = EvidenceCandidate(
        source="coverage",
        decision_type="COVERAGE_SKIPPED",
        decision_id=uuid4(),
        subject="Binary Trees",
        description="Topic Binary Trees skipped",
        metric_name="coverage_percentage",
        metric_value=15.0,
    )

    steps = service.build_steps(candidate, citation_doc_name="Algorithm Design Manual")

    assert len(steps) == 4
    assert steps[0].step_order == 1
    assert "[OBSERVATION]" in steps[0].reason
    assert "[EVIDENCE]" in steps[1].reason
    assert "[ANALYSIS]" in steps[2].reason
    assert "[CONCLUSION]" in steps[3].reason
    assert "Algorithm Design Manual" in steps[1].reason
