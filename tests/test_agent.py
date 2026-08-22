import unittest

from mcp import Client

from agent_practice.agent import WorkshopAgent
from agent_practice.mcp_server import mcp
from agent_practice.mcp_tools import MCPTools
from agent_practice.models import DemoModel
from agent_practice.skill import default_skill_path, load_skill


class AgentTests(unittest.IsolatedAsyncioTestCase):
    async def test_demo_model_completes_full_tool_loop(self) -> None:
        async with Client(mcp, raise_exceptions=True) as client:
            agent = WorkshopAgent(
                model=DemoModel(),
                tools=MCPTools(client),
                skill=load_skill(default_skill_path()),
            )
            result = await agent.run(
                "为 12 位初学者设计一场 90 分钟工作坊，预算 600 元。"
            )

        self.assertEqual(result.model_turns, 3)
        self.assertIn("Agent 入门工作坊方案", result.answer)
        self.assertIn("516.00 元", result.answer)
        self.assertEqual(
            [event.message for event in result.events if event.kind == "mcp"],
            [
                "调用 design_workshop_agenda 成功",
                "调用 estimate_workshop_cost 成功",
            ],
        )


if __name__ == "__main__":
    unittest.main()
