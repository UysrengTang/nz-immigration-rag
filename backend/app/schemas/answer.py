from uuid import UUID

from pydantic import Field, HttpUrl

from app.schemas.common import BaseSchema, SourceType


class Citation(BaseSchema):
    chunk_id: UUID
    title: str
    url: HttpUrl
    section_label: str | None = None
    source_type: SourceType


class SourceReference(BaseSchema):
    document_id: UUID
    title: str
    url: HttpUrl
    source_type: SourceType


class AnswerClaim(BaseSchema):
    claim_text: str
    citation_chunk_ids: list[UUID] = Field(default_factory=list)


class AnswerDraft(BaseSchema):
    answer_text: str
    claims: list[AnswerClaim] = Field(default_factory=list)
    disclaimer: str


class FinalResponse(BaseSchema):
    answer_text: str
    grounded: bool
    refusal_reason: str | None = None
    disclaimer: str
    citations: list[Citation] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)
