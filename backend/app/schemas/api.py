from uuid import UUID

from pydantic import Field

from app.schemas.answer import FinalResponse
from app.schemas.common import BaseSchema


class ChatRequest(BaseSchema):
    message: str = Field(min_length=1, max_length=10000)
    session_id: UUID | None = None
    user_id: str | None = None
    debug: bool = False


class ChatResponse(BaseSchema):
    request_id: str
    message_id: str
    query: str
    response: FinalResponse
