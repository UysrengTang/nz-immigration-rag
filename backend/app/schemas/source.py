from datetime import datetime

from pydantic import Field, HttpUrl

from app.schemas.common import BaseSchema, SourceType


class SourceDocument(BaseSchema):
    source_id: str
    source_type: SourceType
    title: str
    url: HttpUrl
    canonical_url: HttpUrl
    section_path: list[str] = Field(default_factory=list)
    raw_content: str
    cleaned_content: str
    content_hash: str
    authority_rank: int = 100
    effective_date: datetime | None = None
    scraped_at: datetime
    metadata: dict[str, object] = Field(default_factory=dict)
