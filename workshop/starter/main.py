from __future__ import annotations

import asyncio


async def run(*, trace: bool = True) -> str:
    # TODO LAB 6：组装 Host。
    #
    # 1. 用 StdioServerParameters 描述 `python -m workshop.starter.mcp_server`。
    # 2. 用 stdio_client(...) 创建 transport，并进入 Client 的 async with。
    # 3. 加载本目录 skills/workshop-planner/SKILL.md。
    # 4. 创建 DemoModel、MCPToolbox 和 LearningAgent。
    # 5. 调用 Agent，返回最终文本。
    raise NotImplementedError("完成 LAB 6：连接所有模块")


def main() -> None:
    print(asyncio.run(run()))


if __name__ == "__main__":
    main()
