from dataclasses import dataclass
from typing import AsyncGenerator, Dict, List, Optional, Protocol, Union

from app.domains.conversation.domain.models import Message


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict


class LLMProvider(Protocol):
    async def stream(
        self,
        messages: List[Message],
        tools_schemas: Optional[List[dict]] = None,
    ) -> AsyncGenerator[Union[str, ToolCall], None]:
        """流式输出 token (str) 或 ToolCall。"""
        ...
