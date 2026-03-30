from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import BaseSchema, RunStatus, SourceType


class IngestionRunRecord(BaseSchema):
    id: UUID | None = None
    status: RunStatus
    source_count: int = 0
    document_count: int = 0
    chunk_count: int = 0
    error_summary: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class IngestionRunItemRecord(BaseSchema):
    id: UUID | None = None
    ingestion_run_id: UUID
    source_type: SourceType
    source_locator: str
    status: RunStatus
    document_id: UUID | None = None
    content_hash: str | None = None
    error_message: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime | None = None


class EvaluationRunRecord(BaseSchema):
    id: UUID | None = None
    dataset_name: str
    status: RunStatus
    metrics: dict[str, object] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class EvaluationResultRecord(BaseSchema):
    id: UUID | None = None
    evaluation_run_id: UUID
    example_id: str
    query: str
    expected_outcome: str | None = None
    actual_answer: str | None = None
    actual_grounded: bool | None = None
    actual_refusal: bool | None = None
    citation_coverage_score: float | None = None
    groundedness_score: float | None = None
    evaluator_notes: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime | None = None
