from __future__ import annotations

import argparse
import asyncio
import json

from mcp import Client
from mcp.server import MCPServer


# 练习 1：先写一个普通 Tool。
def get_weather(city: str) -> str:
    # TODO 1：删除下一行，返回“城市：晴，25°C”。
    raise NotImplementedError("请完成练习 1")


mcp = MCPServer("weather-server")


# TODO 2：在 query_weather 上方添加 @mcp.tool()。
def query_weather(city: str) -> str:
    """查询指定城市的天气。"""
    return get_weather(city)


async def run_mcp_demo() -> None:
    """用 MCP Client 发现并调用 MCP Server 中的 Tool。"""
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
