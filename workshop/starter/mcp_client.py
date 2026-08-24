from __future__ import annotations

from typing import Any

from mcp import Client

from workshop.support import ToolDefinition


class MCPToolbox:
    """Translate MCP types into the small interface used by our Agent."""

    def __init__(self, client: Client, *, trace: bool = False) -> None:
        self.client = client
        self.trace = trace
        self.calls: list[str] = []

    async def list_tools(self) -> list[ToolDefinition]:
        # TODO LAB 3:
        # 1. await self.client.list_tools()
        # 2. Map every MCP Tool to ToolDefinition(name, description, input_schema).
        raise NotImplementedError("完成 LAB 3：通过 MCP 发现工具")

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        # TODO LAB 3:
        # 1. Call self.client.call_tool(name, arguments).
        # 2. Reject result.is_error.
        # 3. Return structured_content serialized as a JSON string.
        # 4. Append name to self.calls so the checkpoint can observe the call.
        raise NotImplementedError("完成 LAB 3：通过 MCP 调用工具")
