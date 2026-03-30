from datetime import datetime
from uuid import UUID

from pydantic import Field, HttpUrl

from app.schemas.common import BaseSchema, SourceType


class ChunkRecord(BaseSchema):
    id: UUID | None = None
    document_id: UUID
    section_id: UUID | None = None
    chunk_index: int = Field(ge=0)
    chunk_text: str
    token_count: int = Field(ge=0)
    embedding: list[float] | None = None
    title: str
    url: HttpUrl
    section_label: str | None = None
    source_type: SourceType
    authority_rank: int = 100
    effective_date: datetime | None = None
    content_hash: str
    prev_chunk_id: UUID | None = None
    next_chunk_id: UUID | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
