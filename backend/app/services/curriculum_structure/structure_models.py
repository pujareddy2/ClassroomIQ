from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class BlockType(str, Enum):
    UNIT = "UNIT"
    MODULE = "MODULE"
    CHAPTER = "CHAPTER"
    SECTION = "SECTION"
    TOPIC = "TOPIC"
    SUBTOPIC = "SUBTOPIC"
    LEARNING_OUTCOME = "LEARNING_OUTCOME"
    COURSE_OUTCOME = "COURSE_OUTCOME"
    PROGRAM_OUTCOME = "PROGRAM_OUTCOME"
    OBJECTIVES = "OBJECTIVES"
    REFERENCES = "REFERENCES"
    ASSIGNMENTS = "ASSIGNMENTS"
    EXERCISES = "EXERCISES"
    APPENDIX = "APPENDIX"
    UNKNOWN = "UNKNOWN"

class MarkerReference(BaseModel):
    marker_type: str
    line_number: int
    marker_number: Optional[int] = None
    character_start: int
    character_end: int

class Block(BaseModel):
    block_id: str
    block_type: BlockType
    start_line: int
    end_line: int
    content: str
    marker_ref: MarkerReference
    parent_id: Optional[str] = None
    order: int

class DocumentStructure(BaseModel):
    document_name: str
    blocks: List[Block]
    metadata: Dict[str, Any]
    processing_stats: Dict[str, Any]
    warnings: List[str]
