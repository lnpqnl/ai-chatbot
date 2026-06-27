from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


@dataclass
class ToolResult:
    success: bool
    data: Optional[str] = None
    error: Optional[str] = None


class Tool(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def parameters_schema(self) -> Dict[str, Any]: ...

    def execute(self, params: Dict[str, Any]) -> ToolResult: ...
