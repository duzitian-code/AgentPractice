from __future__ import annotations

TOPICS = {
    "beginner": [
        "Model：接收 messages，返回文本或 tool_calls",
        "Tool：执行确定、可测试的业务动作",
        "MCP：标准化工具发现与跨进程调用",
        "Skill：用 SKILL.md 保存可复用流程",
        "Agent：编排 Model、Skill 和 Tool 的循环",
    ],
    "intermediate": [
        "Model：结构化输出与工具选择",
        "Tool：契约、幂等性与错误边界",
        "MCP：stdio 与 Streamable HTTP transport",
        "Skill：渐进披露与配套资源",
        "Agent：权限、停止条件、审计与评测",
    ],
}


def recommend_topics(level: str) -> dict[str, object]:
    """Return the concepts that learners at this level should study."""
    if level not in TOPICS:
        raise ValueError("level 必须是 beginner 或 intermediate")
    return {"level": level, "topics": TOPICS[level]}


def calculate_workshop_cost(
    participants: int,
    budget_yuan: float,
) -> dict[str, object]:
    """Calculate material and refreshment costs for a workshop."""
    if participants <= 0:
        raise ValueError("participants 必须大于 0")
    if budget_yuan <= 0:
        raise ValueError("budget_yuan 必须大于 0")

    total = round(participants * (18.0 + 12.0), 2)
    remaining = round(budget_yuan - total, 2)
    return {
        "participants": participants,
        "budget_yuan": round(budget_yuan, 2),
        "total_yuan": total,
        "remaining_yuan": remaining,
        "within_budget": remaining >= 0,
    }
