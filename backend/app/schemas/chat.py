import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: uuid.UUID | None = None

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message cannot be blank")
        return v


class ToolCallTrace(BaseModel):
    tool: str
    input: dict
    summary: str


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    reply: str
    tool_calls: list[ToolCallTrace] = []


class MessageOut(BaseModel):
    role: str
    content: str

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str
    messages: list[MessageOut]

    class Config:
        from_attributes = True


class ConversationSummaryOut(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime

    class Config:
        from_attributes = True
