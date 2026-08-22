from __future__ import annotations

import asyncio
import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from agent_practice.contracts import Message, ModelReply, ToolCall


class DemoModel:
    """A deterministic model substitute so the lab works without an API key."""

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
    ) -> ModelReply:
        del tools
        request = self._user_request(messages)
        called_tools = {
            str(message.get("name"))
            for message in messages
            if message.get("role") == "tool"
        }

        if "design_workshop_agenda" not in called_tools:
            return ModelReply(
                tool_calls=(
                    ToolCall(
                        id="demo-agenda",
                        name="design_workshop_agenda",
                        arguments={
                            "audience_level": self._audience_level(request),
                            "duration_minutes": self._extract_int(
                                request,
                                r"(\d+)\s*(?:分钟|分鐘|minutes?|mins?)",
                                90,
                            ),
                        },
                    ),
                )
            )

        if "estimate_workshop_cost" not in called_tools:
            return ModelReply(
                tool_calls=(
                    ToolCall(
                        id="demo-budget",
                        name="estimate_workshop_cost",
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

        agenda = self._tool_payload(messages, "design_workshop_agenda")
        budget = self._tool_payload(messages, "estimate_workshop_cost")
        return ModelReply(content=self._render_plan(agenda, budget))

    @staticmethod
    def _user_request(messages: list[Message]) -> str:
        for message in messages:
            if message.get("role") == "user":
                content = message.get("content")
                if isinstance(content, str):
                    return content
        raise ValueError("演示模型没有收到用户请求")

    @staticmethod
    def _extract_int(text: str, pattern: str, default: int) -> int:
        match = re.search(pattern, text, re.IGNORECASE)
        return int(match.group(1)) if match else default

    @staticmethod
    def _extract_float(text: str, pattern: str, default: float) -> float:
        match = re.search(pattern, text, re.IGNORECASE)
        return float(match.group(1)) if match else default

    @staticmethod
    def _audience_level(text: str) -> str:
        advanced_markers = ("进阶", "進階", "有经验", "有經驗", "intermediate")
        return "intermediate" if any(marker in text.lower() for marker in advanced_markers) else "beginner"

    @staticmethod
    def _tool_payload(messages: list[Message], tool_name: str) -> dict[str, Any]:
        for message in reversed(messages):
            if message.get("role") != "tool" or message.get("name") != tool_name:
                continue
            content = message.get("content")
            if not isinstance(content, str):
                break
            payload = json.loads(content)
            if (
                isinstance(payload, dict)
                and set(payload) == {"result"}
                and isinstance(payload["result"], dict)
            ):
                return payload["result"]
            if isinstance(payload, dict):
                return payload
            break
        raise ValueError(f"缺少工具 {tool_name} 的结构化结果")

    @staticmethod
    def _render_plan(agenda: dict[str, Any], budget: dict[str, Any]) -> str:
        lines = [
            "# Agent 入门工作坊方案",
            "",
            f"- 对象：{agenda['audience_label']}",
            f"- 时长：{agenda['duration_minutes']} 分钟",
            f"- 人数：{budget['participants']} 人",
            "",
            "## 议程",
        ]
        for index, item in enumerate(agenda["items"], start=1):
            practice = "（动手）" if item["hands_on"] else ""
            lines.append(
                f"{index}. {item['start_minute']:>3}-{item['end_minute']:>3} 分钟："
                f"{item['title']}{practice} — {item['outcome']}"
            )

        status = "预算内" if budget["within_budget"] else "超出预算"
        lines.extend(
            [
                "",
                "## 预算",
                f"- 预计总费用：{budget['total_yuan']:.2f} 元",
                f"- 可用预算：{budget['budget_yuan']:.2f} 元",
                f"- 结论：{status}，差额 {abs(budget['remaining_yuan']):.2f} 元",
                f"- 建议：{budget['recommendation']}",
                "",
                "## 验收标准",
                "- 学员能用一句话区分 Model、Agent、Skill、Tool 与 MCP。",
                "- 学员能追踪一次“模型请求工具 → Agent 调用 MCP → 结果返回模型”的循环。",
                "- 学员能新增一个 MCP Tool，并切换到真实的工具调用模型。",
            ]
        )
        return "\n".join(lines)


class OpenAIChatModel:
    """A dependency-free adapter for OpenAI-compatible Chat Completions APIs."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 60.0,
    ) -> None:
        if not api_key:
            raise ValueError("api_key 不能为空")
        if not model:
            raise ValueError("model 不能为空")
        self._api_key = api_key
        self._model = model
        self._endpoint = f"{base_url.rstrip('/')}/chat/completions"
        self._timeout_seconds = timeout_seconds

    async def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
    ) -> ModelReply:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        response = await asyncio.to_thread(self._post_json, payload)
        return self._parse_reply(response)

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            self._endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(f"模型服务返回 HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"无法连接模型服务: {exc.reason}") from exc

        if not isinstance(data, dict):
            raise RuntimeError("模型服务返回的 JSON 顶层不是对象")
        return data

    @staticmethod
    def _parse_reply(response: dict[str, Any]) -> ModelReply:
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("模型响应缺少 choices")
        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise RuntimeError("模型响应缺少 message")

        raw_content = message.get("content")
        if raw_content is not None and not isinstance(raw_content, str):
            raise RuntimeError("模型响应 content 不是字符串")

        parsed_calls: list[ToolCall] = []
        raw_calls = message.get("tool_calls", [])
        if not isinstance(raw_calls, list):
            raise RuntimeError("模型响应 tool_calls 不是数组")
        for index, raw_call in enumerate(raw_calls):
            if not isinstance(raw_call, dict):
                raise RuntimeError("模型响应包含无效的 tool_call")
            function = raw_call.get("function")
            if not isinstance(function, dict):
                raise RuntimeError("tool_call 缺少 function")
            name = function.get("name")
            raw_arguments = function.get("arguments", "{}")
            if not isinstance(name, str):
                raise RuntimeError("tool_call 缺少函数名")
            if isinstance(raw_arguments, str):
                try:
                    arguments = json.loads(raw_arguments)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(f"工具 {name} 的参数不是有效 JSON") from exc
            else:
                arguments = raw_arguments
            if not isinstance(arguments, dict):
                raise RuntimeError(f"工具 {name} 的参数必须是 JSON 对象")
            parsed_calls.append(
                ToolCall(
                    id=str(raw_call.get("id") or f"call-{index}"),
                    name=name,
                    arguments=arguments,
                )
            )

        return ModelReply(content=raw_content, tool_calls=tuple(parsed_calls))
