from uuid import UUID

from pydantic import Field, HttpUrl

from app.schemas.common import BaseSchema, SourceType


class RetrievalFilters(BaseSchema):
    source_types: list[SourceType] = Field(default_factory=list)
    document_ids: list[UUID] = Field(default_factory=list)
    authority_rank_max: int | None = None


class RetrievedChunk(BaseSchema):
    chunk_id: UUID
    document_id: UUID
    title: str
    url: HttpUrl
    section_label: str | None = None
    source_type: SourceType
    chunk_text: str
    retrieval_score: float | None = None
    rerank_score: float | None = None
    authority_rank: int | None = None
    is_neighbor_expansion: bool = False


class EvidenceSufficiency(BaseSchema):
    is_sufficient: bool
    confidence_label: str
    reasons: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
