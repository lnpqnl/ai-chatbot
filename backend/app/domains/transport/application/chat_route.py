import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from sse_starlette.sse import EventSourceResponse

from app.domains.agent.application.agent_service import run_agent
from app.domains.transport.domain.events import (
    DoneEvent,
    TokenEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from app.domains.transport.infrastructure.sse_formatter import format_sse, format_error
from app.domains.conversation.application import conversation_service
from app.domains.conversation.domain.models import Message

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message 不能为空")
        return v

    @field_validator("conversation_id")
    @classmethod
    def conversation_id_is_uuid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                UUID(v)
            except ValueError:
                raise ValueError("conversation_id 必须是合法 UUID")
        return v


@router.post("/api/chat")
async def chat(req: ChatRequest):
    # 获取或创建会话
    conv, is_new = conversation_service.get_or_create(req.conversation_id)

    # 如果传了 conversation_id 但不存在，返回 404
    if req.conversation_id and is_new:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 追加 user message
    conversation_service.append_message(conv.id, Message(role="user", content=req.message))
    messages = conversation_service.get_messages(conv.id)

    async def event_generator():
        try:
            collected = ""
            async for event in run_agent(messages):
                if isinstance(event, TokenEvent):
                    collected += event.token
                    yield format_sse(event)
                elif isinstance(event, (ToolCallEvent, ToolResultEvent)):
                    yield format_sse(event)
                elif isinstance(event, DoneEvent):
                    if collected:
                        conversation_service.append_message(
                            conv.id, Message(role="assistant", content=collected)
                        )
                    yield format_sse(event, conversation_id=conv.id)
        except Exception as e:
            logger.exception("SSE stream error")
            yield format_error(str(e))

    return EventSourceResponse(event_generator())
