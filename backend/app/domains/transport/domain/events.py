from dataclasses import dataclass


@dataclass
class TokenEvent:
    token: str


@dataclass
class ToolCallEvent:
    tool_call_id: str
    name: str
    arguments: dict


@dataclass
class ToolResultEvent:
    tool_call_id: str
    name: str
    result: str
    success: bool


@dataclass
class DoneEvent:
    pass
