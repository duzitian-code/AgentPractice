from __future__ import annotations

from mcp.server import MCPServer

from workshop.solution import tools

mcp = MCPServer(
    "agent-lab",
    instructions="提供 Agent 学习主题和工作坊预算工具。",
)


@mcp.tool()
def recommend_topics(level: str = "beginner") -> dict[str, object]:
    """按学习者水平推荐 Model、Tool、MCP、Skill 和 Agent 主题。"""
    return tools.recommend_topics(level)


@mcp.tool()
def calculate_workshop_cost(
    participants: int,
    budget_yuan: float,
) -> dict[str, object]:
    """计算工作坊材料和茶歇费用，并判断是否超出预算。"""
    return tools.calculate_workshop_cost(participants, budget_yuan)


if __name__ == "__main__":
    mcp.run()
