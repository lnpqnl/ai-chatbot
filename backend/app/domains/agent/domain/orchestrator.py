import json
from dataclasses import dataclass
from typing import AsyncGenerator, List, Optional

from app.domains.conversation.domain.models import Message
from app.domains.llm_gateway.domain.provider import ToolCall
from app.domains.tools.domain.registry import ToolRegistry
from app.domains.transport.domain.events import (
    DoneEvent,
    TokenEvent,
    ToolCallEvent,
    ToolResultEvent,
)


MAX_ITERATIONS = 5


async def orchestrate(
    messages: List[Message],
    registry: ToolRegistry,
    provider,
) -> AsyncGenerator:
    """
    Agent 编排循环：LLM → 判断工具调用 → 执行 → 回传 → 再调 LLM。
    yield TokenEvent / ToolCallEvent / ToolResultEvent / DoneEvent
    """
    tools_schemas = registry.get_schemas()
    working_messages = list(messages)

    for _ in range(MAX_ITERATIONS):
        collected_text = ""
        tool_calls_in_round: List[ToolCall] = []

        async for chunk in provider.stream(working_messages, tools_schemas):
            if isinstance(chunk, ToolCall):
                tool_calls_in_round.append(chunk)
            elif isinstance(chunk, str):
                collected_text += chunk
                yield TokenEvent(token=chunk)

        # 如果没有工具调用，本轮结束
        if not tool_calls_in_round:
            yield DoneEvent()
            return

        # 处理工具调用
        # 先将 assistant tool_calls 追加到 messages
        working_messages.append(Message(
            role="assistant",
            content="",
            tool_calls=[{"id": tc.id, "name": tc.name, "arguments": tc.arguments} for tc in tool_calls_in_round],
        ))

        for tc in tool_calls_in_round:
            yield ToolCallEvent(tool_call_id=tc.id, name=tc.name, arguments=tc.arguments)

            # 执行工具
            tool = registry.get_by_name(tc.name)
            if tool is None:
                result_str = f"工具 {tc.name} 不存在"
                success = False
            else:
                try:
                    result = tool.execute(tc.arguments)
                    result_str = result.data if result.success else (result.error or "未知错误")
                    success = result.success
                except Exception as e:
                    result_str = f"工具执行异常: {e}"
                    success = False

            yield ToolResultEvent(tool_call_id=tc.id, name=tc.name, result=result_str, success=success)

            # 将 tool result 追加到 messages
            working_messages.append(Message(
                role="tool",
                content=result_str,
                tool_call_id=tc.id,
            ))

    # 超过最大循环
    yield DoneEvent()
