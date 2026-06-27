from typing import AsyncGenerator, List, Union

from app.domains.agent.domain.orchestrator import orchestrate
from app.domains.llm_gateway.infrastructure.factory import create_provider
from app.domains.tools.infrastructure.setup import tool_registry
from app.domains.conversation.domain.models import Message
from app.domains.transport.domain.events import (
    DoneEvent,
    TokenEvent,
    ToolCallEvent,
    ToolResultEvent,
)


async def run_agent(
    messages: List[Message],
) -> AsyncGenerator[Union[TokenEvent, ToolCallEvent, ToolResultEvent, DoneEvent], None]:
    """Agent 应用层入口：组装依赖并执行编排循环。"""
    provider = create_provider()
    async for event in orchestrate(messages, tool_registry, provider):
        yield event
