from uuid import uuid4

from app.schemas.answer import FinalResponse
from app.schemas.api import ChatRequest, ChatResponse


class ChatService:
    """Thin application service placeholder for the future LangGraph workflow."""

    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        response = FinalResponse(
            answer_text=(
                "Chat orchestration is not implemented yet. "
                "This endpoint currently validates the request and returns the "
                "MVP response schema."
            ),
            grounded=False,
            refusal_reason="workflow_not_implemented",
            disclaimer=(
                "Information only. This assistant does not provide personalized "
                "immigration or legal advice."
            ),
            citations=[],
            sources=[],
        )

        return ChatResponse(
            request_id=str(uuid4()),
            message_id=str(uuid4()),
            query=request.message,
            response=response,
        )
