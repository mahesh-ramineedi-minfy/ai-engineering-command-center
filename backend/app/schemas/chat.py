import uuid

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: uuid.UUID | None = None


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
