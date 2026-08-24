from __future__ import annotations


def recommend_topics(level: str) -> dict[str, object]:
    """Return the concepts that learners at this level should study."""
    # TODO LAB 1:
    # 1. Accept only "beginner" and "intermediate".
    # 2. Return {"level": level, "topics": [...]}.
    # 3. Beginner topics must include Model, Tool, MCP, Skill, and Agent.
    raise NotImplementedError("完成 LAB 1：实现 recommend_topics")


def calculate_workshop_cost(
    participants: int,
    budget_yuan: float,
) -> dict[str, object]:
    """Calculate material and refreshment costs for a workshop."""
    # TODO LAB 1:
    # - Validate participants > 0 and budget_yuan > 0.
    # - Materials cost 18 yuan/person; refreshments cost 12 yuan/person.
    # - Return participants, budget_yuan, total_yuan, remaining_yuan,
    #   and within_budget.
    raise NotImplementedError("完成 LAB 1：实现 calculate_workshop_cost")
