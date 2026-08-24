from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mcp import Client

from tool_mcp import mcp


def read_skill_metadata(path: Path) -> dict[str, str]:
    """Read only the Skill frontmatter during initial discovery."""
    metadata: dict[str, str] = {}

    with path.open(encoding="utf-8") as skill_file:
        if skill_file.readline().strip() != "---":
            raise RuntimeError("SKILL.md 缺少 YAML frontmatter")

        for line in skill_file:
            stripped = line.strip()
            if stripped == "---":
                break

            key, separator, value = stripped.partition(":")
            if separator:
                metadata[key.strip()] = value.strip()
        else:
            raise RuntimeError("SKILL.md 的 YAML frontmatter 未结束")

    for field in ("name", "description"):
        if not metadata.get(field) or "TODO" in metadata[field]:
            raise RuntimeError(f"SKILL.md 的 {field} 尚未完成")

    return {
        "name": metadata["name"],
        "description": metadata["description"],
    }


def load_skill(path: Path, expected_name: str) -> str:
    """Load the complete Skill only after the Model selects it."""
    metadata = read_skill_metadata(path)
    if metadata["name"] != expected_name:
        raise RuntimeError(f"未找到 Skill：{expected_name}")

    content = path.read_text(encoding="utf-8")
    if "TODO" in content:
        raise RuntimeError("SKILL.md 尚未完成")
    return content


async def search_mcp_tools(client: Client, query: str) -> list[dict]:
    """Discover MCP Tools on demand and return matching Model Schemas."""
    normalized_query = query.strip().casefold()
    if not normalized_query:
        raise ValueError("Tool 搜索词不能为空")

    discovered = (await client.list_tools()).tools
    matched = [
        tool
        for tool in discovered
        if normalized_query
        in f"{tool.name} {tool.description or ''}".casefold()
    ]
    if not matched:
        raise RuntimeError(f"没有发现匹配的 Tool：{query}")

    return [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
        }
        for tool in matched
    ]


async def demo_model(
    messages: list[dict],
    available_skills: list[dict[str, str]],
    tools: list[dict],
) -> dict:
    """Simulate Model choices for Skill loading, Tool search, and Tool Calls."""
    print("\n[Model 收到]")
    print(
        json.dumps(
            {
                "messages": messages,
                "available_skills": available_skills,
                "tools": tools,
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    question = next(
        message["content"]
        for message in messages
        if message["role"] == "user"
    )
    matching_skill = next(
        (
            skill
            for skill in available_skills
            if "天气" in question and "天气" in skill["description"]
        ),
        None,
    )
    if matching_skill is None:
        return {"content": "Model 没有找到适合这个问题的 Skill。"}

    loaded_skill_names = {
        message.get("name")
        for message in messages
        if message["role"] == "system"
    }
    if matching_skill["name"] not in loaded_skill_names:
        return {"load_skill": {"name": matching_skill["name"]}}

    if not tools:
        return {"tool_search": {"query": "weather"}}

    if messages[-1]["role"] == "tool":
        tool_data = json.loads(messages[-1]["content"])
        return {"content": f"Model 根据 Tool 结果回答：{tool_data['result']}"}

    return {
        "tool_call": {
            "name": "query_weather",
            "arguments": {"city": "上海"},
        }
    }


async def run_agent(question: str) -> str:
    """Run the Model decision -> Runtime action -> observation loop."""
    skill_path = Path(__file__).parent / "SKILL.md"
    available_skills = [read_skill_metadata(skill_path)]
    messages = [{"role": "user", "content": question}]
    model_tools: list[dict] = []

    async with Client(mcp, raise_exceptions=True) as client:
        for _ in range(5):
            # TODO 4A: call the Model with messages, Skill metadata, and loaded Tools.
            reply = None
            if reply is None:
                raise NotImplementedError("请完成 TODO 4A")

            print("\n[Model 返回]")
            print(json.dumps(reply, ensure_ascii=False, indent=2))

            if "content" in reply:
                return str(reply["content"])

            if "load_skill" in reply:
                skill_name = reply["load_skill"]["name"]

                # TODO 4B: load the selected Skill and add it as a system message.
                skill = None
                if skill is None:
                    raise NotImplementedError("请完成 TODO 4B")
                messages.insert(
                    0,
                    {
                        "role": "system",
                        "name": skill_name,
                        "content": skill,
                    },
                )
                print(f"\n[Agent Runtime] 已加载 Skill：{skill_name}")
                continue

            if "tool_search" in reply:
                query = reply["tool_search"]["query"]

                # TODO 4C: discover matching Tools through MCP on demand.
                model_tools = []
                if not model_tools:
                    raise NotImplementedError("请完成 TODO 4C")
                print(
                    "\n[Agent Runtime] 已发现 Tools：",
                    ", ".join(tool["name"] for tool in model_tools),
                )
                continue

            call = reply["tool_call"]
            messages.append({"role": "assistant", "tool_call": call})

            # TODO 4D: execute the Model-requested Tool through the MCP Client.
            result = None
            if result is None:
                raise NotImplementedError("请完成 TODO 4D")

            # TODO 4E: append the Tool result as a role="tool" observation.
            raise NotImplementedError("请完成 TODO 4E")

    raise RuntimeError("Agent 超过最大循环次数")


if __name__ == "__main__":
    answer = asyncio.run(run_agent("上海天气怎么样？"))
    print(f"\n[最终答案]\n{answer}")
