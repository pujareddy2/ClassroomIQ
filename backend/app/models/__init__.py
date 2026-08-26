from app.models.institution import Institution
from app.models.user import User
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.course import Course
from app.models.academic_term import AcademicTerm
from app.models.curriculum import Curriculum
from app.models.topic import Topic
from app.models.reference_material import ReferenceMaterial
from app.models.reference_chunk import ReferenceChunk
from app.models.topic_reference import TopicReference
from app.models.lecture_session import LectureSession
from app.models.recording import Recording
from app.models.transcript import Transcript
from app.models.transcript_segment import TranscriptSegment
from app.models.transcript_chunk import TranscriptChunk
from app.models.transcript_topic_mapping import TranscriptTopicMapping
from app.models.validation_flag import ValidationFlag
from app.models.review_decision import ReviewDecision
from app.models.report import Report
from app.models.validation_result import ValidationResult
from app.models.validation_evidence import ValidationEvidence
from app.models.validation_summary import ValidationSummary
from app.models.coverage_result import CoverageResult
from app.models.coverage_detail import CoverageDetail
from app.models.coverage_timeline import CoverageTimeline
from app.models.coverage_summary import CoverageSummary
from app.models.teaching_intelligence import (
    TeachingScoreWeight,
    TeachingAnalysis,
    TeachingSummary,
    TeachingExplanation,
    TeachingExample,
    TeachingStructure,
    TeachingInteraction,
)
from app.models.recommendation_engine import (
    RecAnalysis,
    RecItem,
    RecEvidence,
    RecPriority,
    RecWeekly,
    RecMonthly,
    RecSummary,
)
from app.models.explanation_engine import (
    ExplanationRecord,
    EvidenceItem,
    TranscriptEvidence,
    ReferenceCitation,
    ConfidenceBreakdown,
    ReasoningStep,
    ExplanationSummary,
)
from app.models.analysis_job import AnalysisJob

__all__ = [
    "Institution",
    "User",
    "Department",
    "Faculty",
    "Course",
    "AcademicTerm",
    "Curriculum",
    "Topic",
    "ReferenceMaterial",
    "ReferenceChunk",
    "TopicReference",
    "LectureSession",
    "Recording",
    "Transcript",
    "TranscriptSegment",
    "TranscriptChunk",
    "TranscriptTopicMapping",
    "ValidationFlag",
    "ReviewDecision",
    "Report",
    "ValidationResult",
    "ValidationEvidence",
    "ValidationSummary",
    "CoverageResult",
    "CoverageDetail",
    "CoverageTimeline",
    "CoverageSummary",
    "TeachingScoreWeight",
    "TeachingAnalysis",
    "TeachingSummary",
    "TeachingExplanation",
    "TeachingExample",
    "TeachingStructure",
    "TeachingInteraction",
    "RecAnalysis",
    "RecItem",
    "RecEvidence",
    "RecPriority",
    "RecWeekly",
    "RecMonthly",
    "RecSummary",
    "ExplanationRecord",
    "EvidenceItem",
    "TranscriptEvidence",
    "ReferenceCitation",
    "ConfidenceBreakdown",
    "ReasoningStep",
    "ExplanationSummary",
    "AnalysisJob",
]
