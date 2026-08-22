from __future__ import annotations

import json
from typing import Any

from mcp import Client
from mcp.types import TextContent

from agent_practice.contracts import ToolOutcome, ToolSpec


class MCPTools:
    """Adapts MCP's typed client API to the agent's small tool interface."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def list_tools(self) -> list[ToolSpec]:
        result = await self._client.list_tools()
        return [
            ToolSpec(
                name=tool.name,
                description=tool.description or tool.title or tool.name,
                input_schema=tool.input_schema,
            )
            for tool in result.tools
        ]

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> ToolOutcome:
        result = await self._client.call_tool(name, arguments)
        if result.structured_content is not None:
            payload: Any = result.structured_content
        else:
            payload = {
                "content": [
                    block.text
                    for block in result.content
                    if isinstance(block, TextContent)
                ]
            }

        if result.is_error:
            payload = {
                "is_error": True,
                "details": payload,
            }
        return ToolOutcome(
            content=json.dumps(payload, ensure_ascii=False),
            is_error=result.is_error,
        )
