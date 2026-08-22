from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

Message = dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    """A tool invocation requested by a model."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ModelReply:
    """The normalized output of any supported chat model."""

    content: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()


class ChatModel(Protocol):
    """The small model interface required by the agent loop."""

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
    ) -> ModelReply:
        """Return text, tool calls, or both."""


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]

    def as_model_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


@dataclass(frozen=True)
class ToolOutcome:
    content: str
    is_error: bool


@dataclass(frozen=True)
class AgentEvent:
    kind: str
    message: str


@dataclass(frozen=True)
class AgentResult:
    answer: str
    events: tuple[AgentEvent, ...]
    model_turns: int
