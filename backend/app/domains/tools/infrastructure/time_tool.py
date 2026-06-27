from datetime import datetime
from typing import Any, Dict

import pytz

from app.domains.tools.domain.base import ToolResult


class TimeTool:
    @property
    def name(self) -> str:
        return "get_current_time"

    @property
    def description(self) -> str:
        return "获取指定时区的当前时间"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "时区名称，例如 Asia/Shanghai",
                    "default": "Asia/Shanghai",
                }
            },
        }

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        tz_name = params.get("timezone", "Asia/Shanghai")
        try:
            tz = pytz.timezone(tz_name)
        except pytz.exceptions.UnknownTimeZoneError:
            return ToolResult(success=False, error=f"未知时区: {tz_name}")

        now = datetime.now(tz)
        formatted = now.strftime("%Y-%m-%d %H:%M:%S %Z")
        return ToolResult(success=True, data=formatted)
