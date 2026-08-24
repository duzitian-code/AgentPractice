from __future__ import annotations

import argparse
import asyncio
import json

from mcp import Client
from mcp.server import MCPServer


# Exercise 1: start with a regular Tool function.
def get_weather(city: str) -> str:
    # TODO 1: replace the next line with the sample weather result.
    raise NotImplementedError("请完成练习 1")


mcp = MCPServer("weather-server")


# TODO 2: add @mcp.tool() above query_weather.
def query_weather(city: str) -> str:
    """Return the weather for a city."""
    return get_weather(city)


async def run_mcp_demo() -> None:
    """Use an MCP Client to discover and call a Tool on the MCP Server."""
    async with Client(mcp, raise_exceptions=True) as client:
        tools = (await client.list_tools()).tools
        print(
            "MCP 发现的工具：",
            json.dumps(
                [
                    {
                        "name": tool.name,
                        "input_schema": tool.input_schema,
                    }
                    for tool in tools
                ],
                ensure_ascii=False,
                indent=2,
            ),
        )

        if not tools:
            raise RuntimeError("没有发现工具，请完成练习 2")

        result = await client.call_tool("query_weather", {"city": "上海"})
        print(
            "MCP 返回：",
            json.dumps(result.structured_content, ensure_ascii=False),
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("tool", "mcp"))
    args = parser.parse_args()

    if args.mode == "tool":
        print(get_weather("上海"))
    else:
        asyncio.run(run_mcp_demo())


if __name__ == "__main__":
    main()
