from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SourceType(StrEnum):
    INZ_WEBSITE = "inz_website"
    OPERATIONAL_MANUAL = "operational_manual"


class DocumentStatus(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    FAILED = "failed"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        extra="forbid",
    )


class TimestampedSchema(BaseSchema):
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MetadataSchema(BaseSchema):
    metadata: dict[str, object] = Field(default_factory=dict)


class ResourceRef(BaseSchema):
    id: UUID
