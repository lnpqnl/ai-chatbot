import json
import uuid
from typing import AsyncGenerator, List, Optional, Union

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
    AIMessage,
    ToolMessage,
)

from app.domains.conversation.domain.models import Message
from app.domains.llm_gateway.domain.provider import ToolCall
from app.shared.config import get_openai_api_key, get_openai_base_url, get_openai_model


def _to_langchain_messages(messages: List[Message]):
    """将内部 Message 转为 langchain 消息格式。"""
    lc_messages = []
    for msg in messages:
        if msg.role == "system":
            lc_messages.append(SystemMessage(content=msg.content))
        elif msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            if msg.tool_calls:
                tc_list = []
                for tc in msg.tool_calls:
                    tc_list.append({
                        "id": tc["id"],
                        "name": tc["name"],
                        "args": tc["arguments"],
                        "type": "tool_call",
                    })
                lc_messages.append(AIMessage(content=msg.content or "", tool_calls=tc_list))
            else:
                lc_messages.append(AIMessage(content=msg.content))
        elif msg.role == "tool":
            lc_messages.append(ToolMessage(content=msg.content, tool_call_id=msg.tool_call_id or ""))
    return lc_messages


def _to_langchain_tools(schemas: List[dict]):
    """将内部 tool schema 转为 langchain bind_tools 格式。"""
    tools = []
    for s in schemas:
        tools.append({
            "type": "function",
            "function": {
                "name": s["name"],
                "description": s["description"],
                "parameters": s["parameters"],
            },
        })
    return tools


class OpenAIProvider:
    def __init__(self) -> None:
        kwargs = {
            "model": get_openai_model(),
            "api_key": get_openai_api_key(),
            "streaming": True,
        }
        base_url = get_openai_base_url()
        if base_url:
            kwargs["base_url"] = base_url
        self._model = ChatOpenAI(**kwargs)

    async def stream(
        self,
        messages: List[Message],
        tools_schemas: Optional[List[dict]] = None,
    ) -> AsyncGenerator[Union[str, ToolCall], None]:
        lc_messages = _to_langchain_messages(messages)

        model = self._model
        if tools_schemas:
            lc_tools = _to_langchain_tools(tools_schemas)
            model = model.bind_tools(lc_tools)

        # 聚合 tool_calls（流式中可能分多个 chunk 到达）
        pending_tool_calls = {}  # index -> {id, name, arguments_str}

        async for chunk in model.astream(lc_messages):
            # 文本 token
            if chunk.content:
                yield chunk.content

            # tool_calls chunk 聚合
            if hasattr(chunk, "tool_call_chunks"):
                for tc_chunk in chunk.tool_call_chunks:
                    idx = tc_chunk.get("index", 0)
                    if idx not in pending_tool_calls:
                        pending_tool_calls[idx] = {
                            "id": tc_chunk.get("id", f"call_{uuid.uuid4().hex[:8]}"),
                            "name": tc_chunk.get("name", ""),
                            "arguments_str": "",
                        }
                    if tc_chunk.get("name"):
                        pending_tool_calls[idx]["name"] = tc_chunk["name"]
                    if tc_chunk.get("id"):
                        pending_tool_calls[idx]["id"] = tc_chunk["id"]
                    if tc_chunk.get("args"):
                        pending_tool_calls[idx]["arguments_str"] += tc_chunk["args"]

        # 流结束后，输出聚合的 tool_calls
        for idx in sorted(pending_tool_calls):
            tc = pending_tool_calls[idx]
            try:
                arguments = json.loads(tc["arguments_str"]) if tc["arguments_str"] else {}
            except json.JSONDecodeError:
                arguments = {}
            yield ToolCall(id=tc["id"], name=tc["name"], arguments=arguments)
