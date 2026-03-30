from datetime import datetime
from uuid import UUID

from pydantic import Field, HttpUrl

from app.schemas.common import BaseSchema, DocumentStatus, SourceType


class DocumentRecord(BaseSchema):
    id: UUID | None = None
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
    status: DocumentStatus = DocumentStatus.ACTIVE
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DocumentSectionRecord(BaseSchema):
    id: UUID | None = None
    document_id: UUID
    parent_section_id: UUID | None = None
    section_key: str
    heading: str | None = None
    section_path_text: str
    level: int = Field(ge=0)
    ordinal: int = Field(ge=0)
    body_text: str
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime | None = None
