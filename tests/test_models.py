import unittest

from agent_practice.models import OpenAIChatModel


class OpenAIChatModelTests(unittest.TestCase):
    def test_parses_tool_call_response(self) -> None:
        reply = OpenAIChatModel._parse_reply(
            {
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "function": {
                                        "name": "estimate_workshop_cost",
                                        "arguments": (
                                            '{"participants": 12, "budget_yuan": 600}'
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        )

        self.assertEqual(reply.tool_calls[0].name, "estimate_workshop_cost")
        self.assertEqual(reply.tool_calls[0].arguments["participants"], 12)


if __name__ == "__main__":
    unittest.main()
