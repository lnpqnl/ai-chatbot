from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str
    tool_calls: Optional[List[dict]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Conversation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
