from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProviderCreate(BaseModel):
    name: str
    profession: str
    work_description: str
    reliability_score: float = Field(ge=0.0, le=5.0)
    keywords: list[str] = Field(min_length=5)
    domain: str  # e.g. "tech", "legal", "medical", "finance"


class ProviderDocument(BaseModel):
    name: str
    profession: str
    work_description: str
    reliability_score: float
    keywords: list[str]
    domain: str
    embedding: Optional[list[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProviderResponse(BaseModel):
    id: str
    name: str
    profession: str
    domain: str
    message: str


class ProviderListItem(BaseModel):
    id: str
    name: str
    profession: str
    work_description: str
    reliability_score: float
    keywords: list[str]
    domain: str
