import json
from typing import Union

from app.domains.transport.domain.events import (
    DoneEvent,
    TokenEvent,
    ToolCallEvent,
    ToolResultEvent,
)


def format_sse(event: Union[TokenEvent, ToolCallEvent, ToolResultEvent], conversation_id: str = "") -> dict:
    """将事件对象序列化为 SSE data dict。"""
    if isinstance(event, TokenEvent):
        return {"data": json.dumps({"type": "token", "token": event.token}, ensure_ascii=False)}
    elif isinstance(event, ToolCallEvent):
        return {"data": json.dumps({
            "type": "tool_call",
            "tool_call_id": event.tool_call_id,
            "name": event.name,
            "arguments": event.arguments,
        }, ensure_ascii=False)}
    elif isinstance(event, ToolResultEvent):
        return {"data": json.dumps({
            "type": "tool_result",
            "tool_call_id": event.tool_call_id,
            "name": event.name,
            "result": event.result,
            "success": event.success,
        }, ensure_ascii=False)}
    elif isinstance(event, DoneEvent):
        return {"data": json.dumps({"type": "done", "conversation_id": conversation_id}, ensure_ascii=False)}
    return {}


def format_error(message: str) -> dict:
    return {"data": json.dumps({"type": "error", "message": message}, ensure_ascii=False)}
