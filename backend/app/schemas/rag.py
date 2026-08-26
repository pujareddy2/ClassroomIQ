from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Academic query text or topic to search")
    course_id: Optional[UUID] = Field(None, description="Optional filter by course UUID")
    topic_id: Optional[UUID] = Field(None, description="Optional filter by curriculum topic UUID")
    reference_material_id: Optional[UUID] = Field(None, description="Optional filter by specific reference document UUID")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of relevant evidence chunks to retrieve (max 20)")


class RAGEvidenceItemSchema(BaseModel):
    chunk_id: UUID
    reference_material_id: UUID
    document_title: str
    author: Optional[str] = None
    edition: Optional[str] = None
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    chunk_text: str
    vector_score: float
    keyword_score: float
    final_score: float


class RAGQueryResponse(BaseModel):
    status: str = "SUCCESS"
    query: str
    total_results: int
    retrieval_mode: str = "semantic"
    processing_time_seconds: float = 0.0
    evidence: List[RAGEvidenceItemSchema]


class RAGIndexResponse(BaseModel):
    status: str = "SUCCESS"
    message: str = "Reference material indexed successfully"
    reference_material_id: UUID
    chunks_created: int
    total_words: int = 0
    embedding_dimension: int = 384
    retrieval_mode: str = "semantic"
    processing_time_seconds: float = 0.0
    processing_status: str = "INDEXED"


class RAGStatusResponse(BaseModel):
    status: str = "SUCCESS"
    reference_material_id: UUID
    processing_status: str
    total_chunks: int
    embedded_chunks: int
    failed_chunks: int = 0
    embedding_dimension: int = 384
    retrieval_mode: str = "semantic"


class RAGChunkItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: UUID
    chunk_index: int
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    word_count: int
    chunk_text: str
    has_embedding: bool = True
    status: str = "ACTIVE"


class RAGChunksListResponse(BaseModel):
    status: str = "SUCCESS"
    reference_material_id: UUID
    total_chunks: int
    chunks: List[RAGChunkItemSchema]
