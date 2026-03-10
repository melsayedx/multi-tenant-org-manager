from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    action: str
    entity_type: str
    entity_id: UUID
    details: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMessage(BaseModel):
    role: Literal["user", "model"]
    text: str


class ChatbotRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    stream: bool = False
    history: list[ChatMessage] = []


class ChatbotResponse(BaseModel):
    answer: str
