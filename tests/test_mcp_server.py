import sys
import unittest

from mcp import Client, StdioServerParameters, stdio_client

from agent_practice.mcp_server import mcp


class MCPServerTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_transport_discovers_server(self) -> None:
        transport = stdio_client(
            StdioServerParameters(
                command=sys.executable,
                args=["-m", "agent_practice.mcp_server"],
            )
        )
        async with Client(transport) as client:
            tools = await client.list_tools()

        self.assertEqual(len(tools.tools), 2)

    async def test_server_exposes_tools_resource_and_prompt(self) -> None:
        async with Client(mcp, raise_exceptions=True) as client:
            tools = await client.list_tools()
            resources = await client.list_resources()
            prompts = await client.list_prompts()

        self.assertEqual(
            {tool.name for tool in tools.tools},
            {"design_workshop_agenda", "estimate_workshop_cost"},
        )
        self.assertEqual(
            {str(resource.uri) for resource in resources.resources},
            {"workshop://concept-map"},
        )
        self.assertEqual(
            {prompt.name for prompt in prompts.prompts},
            {"review_workshop_plan"},
        )

    async def test_agenda_fills_requested_duration(self) -> None:
        async with Client(mcp, raise_exceptions=True) as client:
            result = await client.call_tool(
                "design_workshop_agenda",
                {
                    "audience_level": "beginner",
                    "duration_minutes": 90,
                },
            )

        self.assertFalse(result.is_error)
        self.assertIsNotNone(result.structured_content)
        payload = result.structured_content or {}
        self.assertEqual(payload["duration_minutes"], 90)
        self.assertEqual(payload["items"][-1]["end_minute"], 90)

    async def test_cost_estimate_reports_remaining_budget(self) -> None:
        async with Client(mcp, raise_exceptions=True) as client:
            result = await client.call_tool(
                "estimate_workshop_cost",
                {"participants": 12, "budget_yuan": 600},
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content or {}
        self.assertEqual(payload["total_yuan"], 516.0)
        self.assertEqual(payload["remaining_yuan"], 84.0)
        self.assertTrue(payload["within_budget"])


if __name__ == "__main__":
    unittest.main()
