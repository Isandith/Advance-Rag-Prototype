from fastapi import APIRouter
from app.models.chat import ChatRequest, ChatResponse
from app.chat.service import chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    return await chat(request)
