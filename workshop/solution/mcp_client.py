from __future__ import annotations

import json
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
        result = await self.client.list_tools()
        definitions = [
            ToolDefinition(
                name=tool.name,
                description=tool.description or tool.name,
                input_schema=tool.input_schema,
            )
            for tool in result.tools
        ]
        if self.trace:
            print("\n=== MCP LIST TOOLS ===")
            print(json.dumps([definition.name for definition in definitions], ensure_ascii=False))
        return definitions

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        if self.trace:
            print(f"\n=== MCP CALL: {name} ===")
            print(json.dumps(arguments, ensure_ascii=False, indent=2))

        result = await self.client.call_tool(name, arguments)
        if result.is_error:
            raise RuntimeError(f"MCP Tool {name} 调用失败: {result.content}")
        if result.structured_content is None:
            raise RuntimeError(f"MCP Tool {name} 没有返回 structured_content")

        self.calls.append(name)
        content = json.dumps(result.structured_content, ensure_ascii=False)
        if self.trace:
            print(f"\n=== MCP RESULT: {name} ===")
            print(json.dumps(result.structured_content, ensure_ascii=False, indent=2))
        return content
