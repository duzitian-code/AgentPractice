from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters, stdio_client

from workshop.solution.agent import LearningAgent
from workshop.solution.mcp_client import MCPToolbox
from workshop.support import DemoModel, load_skill


async def run(*, trace: bool = True) -> str:
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "workshop.solution.mcp_server"],
    )
    skill_path = Path(__file__).parent / "skills" / "workshop-planner" / "SKILL.md"
    skill = load_skill(skill_path)
    if trace:
        print(f"=== HOST LOAD SKILL: {skill.name} ===")

    async with Client(stdio_client(server)) as client:
        model = DemoModel(trace=trace)
        toolbox = MCPToolbox(client, trace=trace)
        agent = LearningAgent(model=model, toolbox=toolbox, skill=skill)
        return await agent.run(
            "为 12 位初学者设计 Agent 学习工作坊，预算 600 元。"
        )


def main() -> None:
    print("\n=== FINAL ANSWER ===")
    print(asyncio.run(run()))


if __name__ == "__main__":
    main()
