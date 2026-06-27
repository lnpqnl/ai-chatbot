from datetime import datetime
from typing import List, Optional, Tuple

from app.domains.conversation.domain.models import Conversation, Message
from app.domains.conversation.infrastructure.memory_repo import conversation_repo


SYSTEM_PROMPT = """你是一个有用的 AI 助手。请简洁地回答用户的问题。

你拥有以下工具：
- get_current_time: 获取指定时区的当前时间。参数: timezone (默认 Asia/Shanghai)

当用户询问时间相关问题时，请使用工具获取准确时间，不要猜测。"""


def get_or_create(conversation_id: Optional[str]) -> Tuple[Conversation, bool]:
    """获取或创建会话。返回 (conversation, is_new)。"""
    if conversation_id and conversation_repo.exists(conversation_id):
        return conversation_repo.get(conversation_id), False

    conv = Conversation()
    conv.messages.append(Message(role="system", content=SYSTEM_PROMPT))
    conversation_repo.save(conv)
    return conv, True


def append_message(conversation_id: str, message: Message) -> None:
    conv = conversation_repo.get(conversation_id)
    if conv is None:
        raise ValueError(f"Conversation {conversation_id} not found")
    conv.messages.append(message)
    conv.updated_at = datetime.utcnow()
    conversation_repo.save(conv)


def get_messages(conversation_id: str) -> List[Message]:
    conv = conversation_repo.get(conversation_id)
    if conv is None:
        raise ValueError(f"Conversation {conversation_id} not found")
    return conv.messages
