import openai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.orchestrator import run_agent
from app.core.database import get_db
from app.core.deps import get_current_manager
from app.core.rate_limit import rate_limit_chat
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ConversationOut, ToolCallTrace

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse, dependencies=[Depends(rate_limit_chat)])
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager),
) -> ChatResponse:
    if request.conversation_id:
        conversation = await db.get(Conversation, request.conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        history_result = await db.execute(
            select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at)
        )
        history = [{"role": m.role, "content": m.content} for m in history_result.scalars().all()]
    else:
        conversation = Conversation(title=request.message[:60])
        db.add(conversation)
        await db.flush()
        history = []

    try:
        reply_text, tool_trace = await run_agent(request.message, history)
    except openai.RateLimitError:
        raise HTTPException(status_code=503, detail="The AI model is rate-limited right now — wait a moment and try again.")
    except openai.APITimeoutError:
        raise HTTPException(status_code=504, detail="The AI model didn't respond in time — try again.")
    except openai.APIError:
        raise HTTPException(status_code=502, detail="The AI model is temporarily unavailable — try again.")

    db.add(Message(conversation_id=conversation.id, role="user", content=request.message))
    db.add(Message(conversation_id=conversation.id, role="assistant", content=reply_text))
    await db.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        reply=reply_text,
        tool_calls=[ToolCallTrace(**t) for t in tool_trace],
    )


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager),
) -> Conversation:
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id).options(selectinload(Conversation.messages))
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("", response_model=list[ConversationOut])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager),
) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .order_by(Conversation.created_at.desc())
        .limit(20)
        .options(selectinload(Conversation.messages))
    )
    return list(result.scalars().all())
