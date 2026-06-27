import asyncio
import re
import uuid
from typing import AsyncGenerator, List, Optional, Union

from app.domains.conversation.domain.models import Message
from app.domains.llm_gateway.domain.provider import ToolCall


TIME_PATTERN = re.compile(r"时间|几点|what time|current time", re.IGNORECASE)


class MockProvider:
    async def stream(
        self,
        messages: List[Message],
        tools_schemas: Optional[List[dict]] = None,
    ) -> AsyncGenerator[Union[str, ToolCall], None]:
        # 取最后一条 user message
        user_msg = ""
        for msg in reversed(messages):
            if msg.role == "user":
                user_msg = msg.content
                break

        # 检查是否为 tool_result 回传
        last_msg = messages[-1] if messages else None
        if last_msg and last_msg.role == "tool":
            reply = f"当前时间是 {last_msg.content}。"
            for char in reply:
                yield char
                await asyncio.sleep(0.05)
            return

        # 检查是否触发工具调用
        if tools_schemas and TIME_PATTERN.search(user_msg):
            yield ToolCall(
                id=f"call_{uuid.uuid4().hex[:8]}",
                name="get_current_time",
                arguments={"timezone": "Asia/Shanghai"},
            )
            return

        # 普通文本回复
        user_count = sum(1 for m in messages if m.role == "user")
        prefix = f"（第{user_count}轮对话）" if user_count > 1 else ""
        reply = f"{prefix}你好！我是 AI 助手，收到了你的消息：{user_msg}"
        for char in reply:
            yield char
            await asyncio.sleep(0.05)
