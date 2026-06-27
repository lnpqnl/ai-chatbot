"""全局工具注册表，启动时注册所有可用工具。"""
from app.domains.tools.domain.registry import ToolRegistry
from app.domains.tools.infrastructure.time_tool import TimeTool

tool_registry = ToolRegistry()
tool_registry.register(TimeTool())
