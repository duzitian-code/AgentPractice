from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from mcp import Client, StdioServerParameters, stdio_client
from mcp.client import Transport

from agent_practice.agent import WorkshopAgent
from agent_practice.mcp_tools import MCPTools
from agent_practice.models import DemoModel, OpenAIChatModel
from agent_practice.skill import default_skill_path, load_skill

DEFAULT_REQUEST = "为 12 位初学者设计一场 90 分钟的 Agent 入门工作坊，预算 600 元。"

CONCEPT_MAP = """\
用户
  |
  v
Host / CLI（接收请求、展示结果）
  |
  v
Agent（编排循环、状态、权限、停止条件）
  |-- 加载 Skill（可复用的流程与规则）
  |-- 调用 Model（推理：回答还是请求工具）
  `-- 使用 MCP Client
          |
          |  JSON-RPC over stdio / Streamable HTTP
          v
      MCP Server（发现与调用能力）
          `-- Tool（执行确定性动作）
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-practice",
        description="Model + Agent + Skill + Tool + MCP 教学项目",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("concepts", help="显示核心模块关系图")

    inspect_parser = subparsers.add_parser("inspect", help="检查 MCP Server 能力")
    inspect_parser.add_argument("--mcp-url", default=os.getenv("AGENT_MCP_URL"))
    inspect_parser.add_argument(
        "--schemas",
        action="store_true",
        help="同时显示工具 JSON Schema",
    )

    run_parser = subparsers.add_parser("run", help="运行工作坊规划 Agent")
    run_parser.add_argument("request", nargs="?", default=DEFAULT_REQUEST)
    run_parser.add_argument(
        "--provider",
        choices=("demo", "openai"),
        default=os.getenv("AGENT_MODEL_PROVIDER", "demo"),
    )
    run_parser.add_argument("--model", default=os.getenv("OPENAI_MODEL"))
    run_parser.add_argument(
        "--base-url",
        default=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )
    run_parser.add_argument("--skill", type=Path)
    run_parser.add_argument("--mcp-url", default=os.getenv("AGENT_MCP_URL"))
    run_parser.add_argument("--max-steps", type=int, default=6)
    run_parser.add_argument("--trace", action="store_true")
    return parser


def _mcp_source(url: str | None) -> str | Transport:
    if url:
        return url
    return stdio_client(
        StdioServerParameters(
            command=sys.executable,
            args=["-m", "agent_practice.mcp_server"],
        )
    )


def _build_model(args: argparse.Namespace) -> DemoModel | OpenAIChatModel:
    if args.provider == "demo":
        return DemoModel()

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("使用 openai provider 前请设置 OPENAI_API_KEY")
    if not args.model:
        raise RuntimeError("使用 openai provider 前请设置 OPENAI_MODEL 或 --model")
    return OpenAIChatModel(
        api_key=api_key,
        model=args.model,
        base_url=args.base_url,
    )


async def _run_agent(args: argparse.Namespace) -> None:
    skill = load_skill(args.skill or default_skill_path())
    model = _build_model(args)
    async with Client(_mcp_source(args.mcp_url)) as client:
        agent = WorkshopAgent(
            model=model,
            tools=MCPTools(client),
            skill=skill,
            max_model_turns=args.max_steps,
        )
        result = await agent.run(args.request)

    if args.trace:
        for event in result.events:
            print(f"[{event.kind.upper()}] {event.message}", file=sys.stderr)
        print(f"[AGENT] 共调用模型 {result.model_turns} 次", file=sys.stderr)
    print(result.answer)


async def _inspect_server(args: argparse.Namespace) -> None:
    async with Client(_mcp_source(args.mcp_url)) as client:
        server_name = client.server_info.name if client.server_info else "unknown"
        print(f"Server: {server_name}")
        print(f"Protocol: {client.protocol_version}")

        tools = (await client.list_tools()).tools
        print("\nTools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description or ''}")
            if args.schemas:
                print(json.dumps(tool.input_schema, ensure_ascii=False, indent=2))

        resources = (await client.list_resources()).resources
        print("\nResources:")
        for resource in resources:
            print(f"- {resource.uri}: {resource.description or resource.name}")

        prompts = (await client.list_prompts()).prompts
        print("\nPrompts:")
        for prompt in prompts:
            print(f"- {prompt.name}: {prompt.description or prompt.title or ''}")


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "concepts":
            print(CONCEPT_MAP)
        elif args.command == "inspect":
            asyncio.run(_inspect_server(args))
        else:
            asyncio.run(_run_agent(args))
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"错误: {exc}\n")


if __name__ == "__main__":
    main()
