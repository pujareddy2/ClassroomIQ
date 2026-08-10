"""
Exceptions for the Curriculum Hierarchy Service.
"""

class CurriculumHierarchyError(Exception):
    """Base exception for curriculum hierarchy errors."""
    pass


class CurriculumNotFoundError(CurriculumHierarchyError):
    """Raised when the specified curriculum ID does not exist."""
    pass


class EmptyCurriculumError(CurriculumHierarchyError):
    """Raised when a curriculum exists but contains no topics/nodes."""
    pass


class InvalidHierarchyError(CurriculumHierarchyError):
    """Raised when unrecoverable structural invalidity is detected."""
    pass


class CircularReferenceError(InvalidHierarchyError):
    """Raised when a circular parent_topic_id relationship is detected."""
    pass


class OrphanNodeError(InvalidHierarchyError):
    """Raised when nodes have invalid parent_topic_id references."""
    pass
