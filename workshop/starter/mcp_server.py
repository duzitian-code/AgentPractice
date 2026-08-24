from __future__ import annotations

from mcp.server import MCPServer

from workshop.starter import tools

mcp = MCPServer(
    "agent-lab",
    instructions="提供 Agent 学习主题和工作坊预算工具。",
)


# TODO LAB 2:
# 1. Add @mcp.tool() so this function is discoverable through MCP.
# 2. Delegate the business calculation to tools.recommend_topics.
def recommend_topics(level: str = "beginner") -> dict[str, object]:
    raise NotImplementedError("完成 LAB 2：把 recommend_topics 暴露为 MCP Tool")


# TODO LAB 2:
# Expose this function as a second MCP Tool.
def calculate_workshop_cost(
    participants: int,
    budget_yuan: float,
) -> dict[str, object]:
    raise NotImplementedError("完成 LAB 2：把 calculate_workshop_cost 暴露为 MCP Tool")


if __name__ == "__main__":
    mcp.run()
