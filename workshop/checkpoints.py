from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Sequence

from mcp import Client

from workshop.support import DemoModel, ModelReply, ToolCall, load_skill


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


async def check_lab_1(package: str) -> None:
    tools = importlib.import_module(f"{package}.tools")
    topics = tools.recommend_topics("beginner")
    require(
        {"Model", "Tool", "MCP", "Skill", "Agent"}
        <= {str(topic).split("：", maxsplit=1)[0] for topic in topics["topics"]},
        "recommend_topics 必须覆盖 Model、Tool、MCP、Skill 和 Agent",
    )
    cost = tools.calculate_workshop_cost(12, 600)
    require(cost["total_yuan"] == 360.0, "12 人的总成本应为 360 元")
    require(cost["remaining_yuan"] == 240.0, "600 元预算应剩余 240 元")
    require(cost["within_budget"] is True, "该方案应在预算内")
    for arguments in ((0, 600), (12, 0)):
        try:
            tools.calculate_workshop_cost(*arguments)
        except ValueError:
            pass
        else:
            raise AssertionError("Tool 必须对非正数参数抛出 ValueError")


async def check_lab_2(package: str) -> None:
    server = importlib.import_module(f"{package}.mcp_server")
    async with Client(server.mcp, raise_exceptions=True) as client:
        listed = await client.list_tools()
        names = {tool.name for tool in listed.tools}
        require(
            names == {"recommend_topics", "calculate_workshop_cost"},
            "MCP Server 必须暴露两个 Tool；检查 @mcp.tool()",
        )
        result = await client.call_tool(
            "calculate_workshop_cost",
            {"participants": 12, "budget_yuan": 600},
        )
    require(not result.is_error, "MCP Tool 调用不应报错")
    require(result.structured_content is not None, "MCP Tool 应返回结构化结果")


async def check_lab_3(package: str) -> None:
    server = importlib.import_module(f"{package}.mcp_server")
    client_module = importlib.import_module(f"{package}.mcp_client")
    async with Client(server.mcp, raise_exceptions=True) as client:
        toolbox = client_module.MCPToolbox(client)
        definitions = await toolbox.list_tools()
        require(len(definitions) == 2, "MCP Client 应发现两个工具")
        require(
            all(definition.input_schema for definition in definitions),
            "每个工具都应保留 MCP 返回的 input_schema",
        )
        content = await toolbox.call_tool(
            "calculate_workshop_cost",
            {"participants": 12, "budget_yuan": 600},
        )
        try:
            await toolbox.call_tool("not_a_real_tool", {})
        except RuntimeError:
            pass
        else:
            raise AssertionError("MCP Client 必须把 Tool 错误显式暴露给调用者")
    payload = json.loads(content)
    if isinstance(payload, dict) and set(payload) == {"result"}:
        payload = payload["result"]
    require(payload["total_yuan"] == 360.0, "MCP Client 应返回 Tool 的结构化结果")


async def check_lab_4(package: str) -> None:
    target = package.rsplit(".", maxsplit=1)[-1]
    skill_path = (
        Path(__file__).parent
        / target
        / "skills"
        / "workshop-planner"
        / "SKILL.md"
    )
    skill = load_skill(skill_path)
    require("TODO" not in skill.description, "请补全 Skill description")
    require(
        "recommend_topics" in skill.instructions,
        "Skill workflow 必须要求调用 recommend_topics",
    )
    require(
        "calculate_workshop_cost" in skill.instructions,
        "Skill workflow 必须要求调用 calculate_workshop_cost",
    )
    require(
        "工具返回" in skill.instructions,
        "Skill 必须说明如何安全处理工具返回值",
    )


async def check_lab_5(package: str) -> None:
    server = importlib.import_module(f"{package}.mcp_server")
    client_module = importlib.import_module(f"{package}.mcp_client")
    agent_module = importlib.import_module(f"{package}.agent")
    target = package.rsplit(".", maxsplit=1)[-1]
    skill = load_skill(
        Path(__file__).parent
        / target
        / "skills"
        / "workshop-planner"
        / "SKILL.md"
    )

    async with Client(server.mcp, raise_exceptions=True) as client:
        toolbox = client_module.MCPToolbox(client)
        model = DemoModel()
        agent = agent_module.LearningAgent(
            model=model,
            toolbox=toolbox,
            skill=skill,
        )
        answer = await agent.run(
            "为 12 位初学者设计 Agent 学习工作坊，预算 600 元。"
        )

        require(model.call_count == 3, "完整循环应调用模型三次")
        require(
            toolbox.calls == ["recommend_topics", "calculate_workshop_cost"],
            "Agent 应按 Model 的请求调用两个 MCP Tool",
        )
        require("学习主题" in answer and "预算" in answer, "最终答案缺少主题或预算")

        class UnknownToolModel:
            async def complete(self, messages, tools):
                return ModelReply(
                    tool_calls=(
                        ToolCall(
                            id="unknown",
                            name="delete_everything",
                            arguments={},
                        ),
                    )
                )

        guarded_agent = agent_module.LearningAgent(
            model=UnknownToolModel(),
            toolbox=client_module.MCPToolbox(client),
            skill=skill,
        )
        try:
            await guarded_agent.run("调用一个不存在的工具")
        except RuntimeError:
            pass
        else:
            raise AssertionError("Agent 必须拒绝 MCP 未提供的工具")

        class LoopingModel:
            async def complete(self, messages, tools):
                return ModelReply(
                    tool_calls=(
                        ToolCall(
                            id="again",
                            name="recommend_topics",
                            arguments={"level": "beginner"},
                        ),
                    )
                )

        bounded_agent = agent_module.LearningAgent(
            model=LoopingModel(),
            toolbox=client_module.MCPToolbox(client),
            skill=skill,
            max_turns=1,
        )
        try:
            await bounded_agent.run("一直调用工具")
        except RuntimeError:
            pass
        else:
            raise AssertionError("Agent 必须在 max_turns 后停止")


async def check_lab_6(package: str) -> None:
    main_module = importlib.import_module(f"{package}.main")
    answer = await main_module.run(trace=False)
    require("Agent 学习工作坊" in answer, "Host 没有返回完整 Agent 答案")


CHECKS = {
    1: check_lab_1,
    2: check_lab_2,
    3: check_lab_3,
    4: check_lab_4,
    5: check_lab_5,
    6: check_lab_6,
}


async def run_checks(target: str, labs: list[int]) -> None:
    package = f"workshop.{target}"
    for lab in labs:
        await CHECKS[lab](package)
        print(f"LAB {lab} PASS")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Agent hands-on lab checkpoints")
    parser.add_argument("--target", choices=("starter", "solution"), default="starter")
    parser.add_argument(
        "--lab",
        choices=("1", "2", "3", "4", "5", "6", "all"),
        default="all",
    )
    args = parser.parse_args(argv)
    labs = list(CHECKS) if args.lab == "all" else [int(args.lab)]

    import asyncio

    try:
        asyncio.run(run_checks(args.target, labs))
    except (
        AssertionError,
        KeyError,
        NotImplementedError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as exc:
        parser.exit(1, f"未通过: {exc}\n")


if __name__ == "__main__":
    main()
