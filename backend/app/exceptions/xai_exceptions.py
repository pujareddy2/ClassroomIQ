"""
Typed exceptions for the Explainable AI Engine.

Raised by services — caught and translated by the API layer (when built).
"""


class ExplanationNotFoundError(Exception):
    """Raised when a requested ExplanationRecord does not exist."""

    def __init__(self, identifier: str, message: str = ""):
        self.identifier = identifier
        super().__init__(message or f"Explanation not found: {identifier}")


class DuplicateExplanationError(Exception):
    """Raised when an ACTIVE explanation already exists for a decision."""

    def __init__(self, decision_source: str, decision_type: str, message: str = ""):
        self.decision_source = decision_source
        self.decision_type = decision_type
        super().__init__(
            message or f"Active explanation already exists for {decision_source}/{decision_type}"
        )


class ExplanationBuildError(Exception):
    """Raised when the ExplanationBuilderService fails to assemble a package."""

    def __init__(self, reason: str, candidate_source: str = "", message: str = ""):
        self.reason = reason
        self.candidate_source = candidate_source
        super().__init__(
            message or f"Explanation build failed [{candidate_source}]: {reason}"
        )
