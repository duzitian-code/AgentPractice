from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

Message = dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ModelReply:
    content: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]

    def for_model(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    instructions: str


class ChatModel(Protocol):
    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
    ) -> ModelReply:
        """Return text, tool calls, or both."""


def load_skill(path: Path) -> Skill:
    """Simulate the host loading an Agent Skills-compatible SKILL.md file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md 必须以 YAML frontmatter 开始")

    try:
        closing = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration as exc:
        raise ValueError("SKILL.md 缺少 YAML frontmatter 结束标记") from exc

    metadata: dict[str, str] = {}
    for line in lines[1:closing]:
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip("'\"")

    name = metadata.get("name", "")
    description = metadata.get("description", "")
    instructions = "\n".join(lines[closing + 1 :]).strip()
    if not name or not description or not instructions:
        raise ValueError("Skill 必须包含 name、description 和 instructions")
    return Skill(name=name, description=description, instructions=instructions)


class DemoModel:
    """A deterministic stand-in that speaks the same tool-calling contract as an LLM."""

    def __init__(self, *, trace: bool = False) -> None:
        self.trace = trace
        self.call_count = 0

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
    ) -> ModelReply:
        self.call_count += 1
        if self.trace:
            self._print(
                f"MODEL INPUT #{self.call_count}",
                {"messages": messages, "tools": tools},
            )

        advertised = {
            tool["function"]["name"]
            for tool in tools
            if isinstance(tool.get("function"), dict)
        }
        required = {"recommend_topics", "calculate_workshop_cost"}
        missing = required - advertised
        if missing:
            raise RuntimeError(f"模型没有收到工具定义: {sorted(missing)}")

        called = {
            str(message.get("name"))
            for message in messages
            if message.get("role") == "tool"
        }
        request = self._user_request(messages)

        if "recommend_topics" not in called:
            reply = ModelReply(
                tool_calls=(
                    ToolCall(
                        id="call-topics",
                        name="recommend_topics",
                        arguments={"level": self._level(request)},
                    ),
                )
            )
        elif "calculate_workshop_cost" not in called:
            reply = ModelReply(
                tool_calls=(
                    ToolCall(
                        id="call-cost",
                        name="calculate_workshop_cost",
                        arguments={
                            "participants": self._extract_int(
                                request,
                                r"(\d+)\s*(?:人|位)",
                                12,
                            ),
                            "budget_yuan": self._extract_float(
                                request,
                                r"(?:预算|預算)[^\d]{0,8}(\d+(?:\.\d+)?)",
                                600.0,
                            ),
                        },
                    ),
                )
            )
        else:
            topics = self._tool_payload(messages, "recommend_topics")
            cost = self._tool_payload(messages, "calculate_workshop_cost")
            topic_lines = "\n".join(f"- {item}" for item in topics["topics"])
            status = "预算内" if cost["within_budget"] else "超出预算"
            reply = ModelReply(
                content=(
                    "# Agent 学习工作坊\n\n"
                    f"## 学习主题\n{topic_lines}\n\n"
                    "## 预算\n"
                    f"- {cost['participants']} 人，共 {cost['total_yuan']:.2f} 元\n"
                    f"- 预算 {cost['budget_yuan']:.2f} 元，结论：{status}\n"
                    f"- 余额：{cost['remaining_yuan']:.2f} 元"
                )
            )

        if self.trace:
            self._print(
                f"MODEL OUTPUT #{self.call_count}",
                {
                    "content": reply.content,
                    "tool_calls": [asdict(call) for call in reply.tool_calls],
                },
            )
        return reply

    @staticmethod
    def _user_request(messages: list[Message]) -> str:
        for message in messages:
            if message.get("role") == "user" and isinstance(message.get("content"), str):
                return str(message["content"])
        raise ValueError("模型输入中缺少 user message")

    @staticmethod
    def _level(text: str) -> str:
        return "intermediate" if any(word in text for word in ("进阶", "有经验")) else "beginner"

    @staticmethod
    def _extract_int(text: str, pattern: str, default: int) -> int:
        match = re.search(pattern, text)
        return int(match.group(1)) if match else default

    @staticmethod
    def _extract_float(text: str, pattern: str, default: float) -> float:
        match = re.search(pattern, text)
        return float(match.group(1)) if match else default

    @staticmethod
    def _tool_payload(messages: list[Message], name: str) -> dict[str, Any]:
        for message in reversed(messages):
            if message.get("role") != "tool" or message.get("name") != name:
                continue
            payload = json.loads(str(message["content"]))
            if isinstance(payload, dict) and set(payload) == {"result"}:
                payload = payload["result"]
            if isinstance(payload, dict):
                return payload
        raise ValueError(f"缺少工具结果: {name}")

    @staticmethod
    def _print(label: str, payload: dict[str, Any]) -> None:
        print(f"\n=== {label} ===")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
