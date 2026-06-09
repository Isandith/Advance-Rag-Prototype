from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    session_id: Optional[str] = None


class ChatDocument(BaseModel):
    session_id: str
    messages: list[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
