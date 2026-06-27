from typing import Dict, Optional

from app.domains.conversation.domain.models import Conversation
from app.domains.conversation.domain.repository import ConversationRepository


class InMemoryConversationRepository:
    """内存实现，满足 ConversationRepository Protocol。"""

    def __init__(self) -> None:
        self._store: Dict[str, Conversation] = {}

    def get(self, conversation_id: str) -> Optional[Conversation]:
        return self._store.get(conversation_id)

    def save(self, conversation: Conversation) -> None:
        self._store[conversation.id] = conversation

    def exists(self, conversation_id: str) -> bool:
        return conversation_id in self._store


# 单例
conversation_repo = InMemoryConversationRepository()
