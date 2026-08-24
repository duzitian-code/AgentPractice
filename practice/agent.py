from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mcp import Client

from tool_mcp import mcp


async def demo_model(messages: list[dict], tools: list[dict]) -> dict:
    """模拟支持 Tool Calling 的模型；真实模型也接收 messages 和 tools。"""
    print("\n[Model 收到]")
    print(json.dumps({"messages": messages, "tools": tools}, ensure_ascii=False, indent=2))

    if messages[-1]["role"] == "user":
        return {
            "tool_call": {
                "name": "query_weather",
                "arguments": {"city": "上海"},
            }
        }

    tool_data = json.loads(messages[-1]["content"])
    return {"content": f"Model 根据 Tool 结果回答：{tool_data['result']}"}


async def run_agent(question: str) -> str:
    """Agent 负责维护消息、执行 Model 请求的 Tool，并控制循环。"""
    skill = (Path(__file__).parent / "SKILL.md").read_text(encoding="utf-8")
    messages = [
        {"role": "system", "content": skill},
        {"role": "user", "content": question},
    ]

    async with Client(mcp, raise_exceptions=True) as client:
        mcp_tools = (await client.list_tools()).tools
        model_tools = [
            {
                "name": tool.name,
                "parameters": tool.input_schema,
            }
            for tool in mcp_tools
        ]

        for _ in range(2):
            # TODO 4A：调用 demo_model，把 messages 和 model_tools 传给它。
            reply = None
            if reply is None:
                raise NotImplementedError("请完成 TODO 4A")

            print("\n[Model 返回]")
            print(json.dumps(reply, ensure_ascii=False, indent=2))

            if "content" in reply:
                return str(reply["content"])

            call = reply["tool_call"]
            messages.append({"role": "assistant", "tool_call": call})

            # TODO 4B：通过 client.call_tool 执行 call 中的工具名和参数。
            result = None
            if result is None:
                raise NotImplementedError("请完成 TODO 4B")

            # TODO 4C：把 Tool 结果作为 role="tool" 的消息加入 messages。
            raise NotImplementedError("请完成 TODO 4C")

    raise RuntimeError("Agent 超过最大循环次数")


if __name__ == "__main__":
    answer = asyncio.run(run_agent("上海天气怎么样？"))
    print(f"\n[最终答案]\n{answer}")
