from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_chat_service
from app.schemas.api import ChatRequest, ChatResponse
from app.services.chat_service import ChatService


router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    return chat_service.handle_chat(request)
