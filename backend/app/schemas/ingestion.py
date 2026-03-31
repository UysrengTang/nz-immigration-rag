from datetime import datetime

from pydantic import Field, HttpUrl

from app.schemas.common import BaseSchema, SourceType


class SourceIngestionPayload(BaseSchema):
    source_id: str
    source_type: SourceType
    title: str
    url: HttpUrl
    canonical_url: HttpUrl | None = None
    raw_content: str
    effective_date: datetime | None = None
    scraped_at: datetime
    authority_rank: int = 100
    metadata: dict[str, object] = Field(default_factory=dict)


class IngestionResult(BaseSchema):
    source_id: str
    document_id: str
    section_count: int
    chunk_count: int
    content_hash: str
