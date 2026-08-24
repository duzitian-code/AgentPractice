# 从零开发 Agent：六关动手实验

## 最终要写出什么

你会实现一个“Agent 学习工作坊规划器”。用户给出人数、水平和预算后：

1. Model 判断需要哪些外部能力。
2. Agent 根据 Model 的 `tool_calls` 调用 MCP Tool。
3. Tool 返回学习主题和预算结果。
4. Agent 把结果以 `role="tool"` 送回 Model。
5. Model 基于真实工具数据给出最终答案。

这不是框架教程。项目只保留必要抽象，让每次数据流动都能被看到。

## 先建立准确的概念

| 模块 | 是什么 | 不是什么 | 本实验文件 |
|---|---|---|---|
| Model | 输入 messages 和 tools，输出文本或 `tool_calls` | 不会直接执行 Python | `support.py` 中的 `DemoModel` |
| Tool | 有明确参数和返回值的确定性能力 | 不是 MCP，也不负责推理 | `starter/tools.py` |
| MCP Server | 用标准协议发布 Tool、Resource、Prompt | 不是模型 | `starter/mcp_server.py` |
| MCP Client | 发现和调用 MCP Server 的能力 | 不决定调用哪个 Tool | `starter/mcp_client.py` |
| Skill | 可复用的任务流程、规则和资源 | 不是可执行函数 | `starter/skills/.../SKILL.md` |
| Agent | 编排 Model、Skill、Tool、状态和停止条件 | 不等于某个 Model | `starter/agent.py` |
| Host | 加载配置并组装运行时 | 不负责领域计算 | `starter/main.py` |

### Tool 与 MCP Tool

`tools.py` 中的函数本来只是普通 Tool：

```text
Python 调用者 -> recommend_topics(...)
```

加上 `@mcp.tool()` 并由 MCP Server 发布后，它才成为可跨进程发现和调用的 MCP Tool：

```text
任意 MCP Host -> MCP Client -> JSON-RPC -> MCP Server -> Tool
```

业务逻辑仍在普通函数中。MCP 层只负责协议、schema、传输和调用。

### Python Agent 与 `.agent.md`

- 本实验的 `LearningAgent` 是运行时代码：它真的维护 messages、执行 Tool、控制循环。
- `.github/agents/agent-lab-coach.agent.md` 是 Copilot Custom Agent 配置：由 Copilot 这个 Host 读取，用来设定角色和工作方式。

两者都叫 Agent，但一个是**运行时实现**，另一个是**现有 Agent 产品的配置**。

## 准备环境

在仓库根目录运行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

只修改 `workshop/starter/`。`workshop/solution/` 是参考答案，建议先尝试，再对照。

每关使用相同命令验收：

```powershell
.\.venv\Scripts\python.exe -m workshop.checkpoints --lab 关卡编号
```

## LAB 0：观察 Model 的接口

先看 `workshop/support.py` 中三个类型：

```python
ModelReply(
    content="直接回答",       # 或者
    tool_calls=(ToolCall(...),)
)
```

Model 每轮只接收两类输入：

```python
messages = [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
]
tools = [
    {
        "type": "function",
        "function": {
            "name": "tool_name",
            "description": "...",
            "parameters": {"type": "object", ...},
        },
    }
]
```

`DemoModel` 是离线模型模拟器。它不执行 Tool，只返回“我想调用什么”的结构化意图。真实 LLM API 的输入输出契约与此相同。

为了让练习离线且结果稳定，`DemoModel` 不理解自然语言 Skill，而是按固定状态返回 Tool Call。此处要观察的是：Skill 确实进入了 system message，以及 Agent 如何处理标准模型响应。最后替换真实模型后，Skill 内容才会直接影响模型决策。

观察完整参考流程：

```powershell
.\.venv\Scripts\python.exe -m workshop.solution.main
```

重点找三段：

1. 第一次 `MODEL INPUT` 同时包含 Skill、用户请求和 MCP Tool schemas。
2. `MODEL OUTPUT` 返回 `tool_calls`，但此时 Tool 还没有执行。
3. 下一次 `MODEL INPUT` 多出一条 `role="tool"` 消息。

## LAB 1：写普通 Tool

编辑：

```text
workshop/starter/tools.py
```

实现两个普通 Python 函数：

- `recommend_topics(level)`：返回与水平匹配的五个核心主题。
- `calculate_workshop_cost(participants, budget_yuan)`：材料 18 元/人，茶歇 12 元/人。

要求：

- 对无效参数明确抛出 `ValueError`。
- 返回 JSON 可序列化的 `dict`。
- Tool 只做确定性业务计算，不读取 Skill，不调用 Model。

验收：

```powershell
.\.venv\Scripts\python.exe -m workshop.checkpoints --lab 1
```

此时你写的是 Tool，但还不是 MCP Tool。它只能被 Python 代码直接导入。

## LAB 2：写 MCP Server

编辑：

```text
workshop/starter/mcp_server.py
```

完成两件事：

1. 用 `@mcp.tool()` 注册两个函数。
2. 函数内部委托 LAB 1 的业务函数，不复制计算逻辑。

MCP SDK 会根据函数的：

- 函数名生成 Tool name；
- docstring 生成 description；
- 类型提示生成 JSON Schema。

验收：

```powershell
.\.venv\Scripts\python.exe -m workshop.checkpoints --lab 2
```

这关使用 MCP 的内存 transport。调用仍会经过真正的 MCP 协议层，只是不创建子进程。

检查问题：

- 删除类型提示后，模型看到的参数 schema 会发生什么？
- 为什么 MCP Server 不应该重新实现成本公式？

## LAB 3：写 MCP Client

编辑：

```text
workshop/starter/mcp_client.py
```

实现：

```python
await client.list_tools()
await client.call_tool(name, arguments)
```

`list_tools()` 返回 MCP 类型；你需要把它转换为 `ToolDefinition`。随后 `ToolDefinition.for_model()` 会将其转换为模型 API 所需的 function schema。

`call_tool()` 需要：

1. 传入 Model 选择的工具名和参数。
2. 检查 `result.is_error`。
3. 把 `structured_content` 序列化为 JSON 字符串。
4. 记录调用名称，便于测试 Agent 是否真的执行了 Tool。

验收：

```powershell
.\.venv\Scripts\python.exe -m workshop.checkpoints --lab 3
```

此时链路是：

```text
测试代码 -> MCP Client -> MCP Server -> Tool
```

还没有 Model，也没有 Agent。

## LAB 4：写 Skill

编辑：

```text
workshop/starter/skills/workshop-planner/SKILL.md
```

Skill 由 YAML frontmatter 和 Markdown 指令组成：

```markdown
---
name: workshop-planner
description: 说明做什么，以及何时使用
---

# Workflow
...
```

补全文件中的所有 TODO，写成真正可交给 Agent 的工作流。至少包含：

1. 何时使用该 Skill。
2. Tool 调用顺序。
3. 最终输出要求。
4. Tool 返回值的安全边界。

验收：

```powershell
.\.venv\Scripts\python.exe -m workshop.checkpoints --lab 4
```

注意：Skill 本身不会执行任何动作。Host 加载它，Agent 把内容放进 Model 的上下文，它才会影响 Model 的决策。

## LAB 5：写 Agent 核心循环

编辑：

```text
workshop/starter/agent.py
```

这是整个实验最重要的一关。实现以下伪代码：

```python
tool_definitions = await mcp.list_tools()
messages = [system_with_skill, user_request]

for turn in range(max_turns):
    reply = await model.complete(messages, tool_definitions)

    if reply has no tool_calls:
        return reply.content

    append assistant tool_calls to messages

    for call in reply.tool_calls:
        validate call.name against discovered tools
        result = await mcp.call_tool(call.name, call.arguments)
        append role="tool" result to messages

raise maximum-turn error
```

必须保留三条安全边界：

- Tool allowlist 来自 MCP `list_tools()`，不能执行模型凭空编出的名字。
- Tool 返回值是数据，不得拼进 system prompt。
- 必须有 `max_turns`，避免模型和工具无限循环。

验收：

```powershell
.\.venv\Scripts\python.exe -m workshop.checkpoints --lab 5
```

验收会确认：

- Model 被调用三次。
- MCP Tool 按 `recommend_topics -> calculate_workshop_cost` 执行。
- 最终答案确实来自第三次 Model 输出。

## LAB 6：写 Host 并用 stdio 投入运行

编辑：

```text
workshop/starter/main.py
```

Host 负责组装，而不是推理。你需要：

1. 用 `StdioServerParameters` 描述 MCP Server 子进程。
2. 用 `stdio_client(...)` 建立 transport。
3. 进入 `Client(...)` 生命周期。
4. 从磁盘加载 `SKILL.md`。
5. 创建 Model、MCPToolbox 和 LearningAgent。
6. 把用户请求交给 Agent。

验收：

```powershell
.\.venv\Scripts\python.exe -m workshop.checkpoints --lab 6
.\.venv\Scripts\python.exe -m workshop.checkpoints --lab all
.\.venv\Scripts\python.exe -m workshop.starter.main
```

LAB 6 会启动一个真实 Python 子进程，并通过 stdin/stdout 传输 MCP JSON-RPC 消息。

## 完整运行时序

```text
Host          Agent           Model        MCP Client      MCP Server      Tool
 |              |               |              |               |            |
 |--load Skill->|               |              |               |            |
 |--run(req)--->|               |              |               |            |
 |              |--list_tools----------------->|--JSON-RPC----->|            |
 |              |<-------names + JSON Schema---|<---------------|            |
 |              |--messages + schemas--------->|               |            |
 |              |<------tool_call--------------|               |            |
 |              |--validate allowlist          |               |            |
 |              |--call_tool------------------>|--JSON-RPC----->|--invoke--->|
 |              |<---------structured result---|<---------------|<-----------|
 |              |--append role=tool----------->|               |            |
 |              |<------next tool_call---------|               |            |
 |              |--call second tool----------->|-------------->|----------->|
 |              |<---------structured result---|<---------------|<-----------|
 |              |--all messages--------------->|               |            |
 |              |<------final content----------|               |            |
 |<--answer------|               |              |               |            |
```

图中最关键的事实：

- Model 只产生 `tool_call`，真正的执行者是 Agent。
- Agent 不需要知道 Tool 的业务实现，只依赖 MCP 提供的 name/schema/result。
- Skill 跟随 system message 进入 Model，但不经过 MCP。
- MCP 连接 Agent/Host 与能力提供方，不负责推理。

## 对照参考答案

每个 starter 文件都在 solution 中有同名实现：

```text
workshop/starter/agent.py
workshop/solution/agent.py
```

验证参考答案：

```powershell
.\.venv\Scripts\python.exe -m workshop.checkpoints --target solution --lab all
```

## 下一步：替换真实 Model

六关完成后，Model 是唯一需要替换的模块。保持 `ChatModel.complete(messages, tools)` 接口不变：

1. 把 `messages` 和 `tools` POST 到支持 Tool Calling 的模型 API。
2. 把响应中的 `content` 和 `tool_calls` 转成 `ModelReply`。
3. 不修改 Tool、MCP Server、Skill 或 Agent loop。

仓库中的 `src/agent_practice/models.py` 提供了 OpenAI 兼容实现，可作为进阶阅读。完整参考应用说明见 `docs/reference-app.md`。

## 完成标准

不看答案，你应该能指出自己代码中的：

1. Tool 业务逻辑。
2. MCP Tool 注册点。
3. MCP Tool 动态发现。
4. Skill 加载位置。
5. 第一次 Model 输入。
6. Model `tool_calls` 的处理位置。
7. `role="tool"` 消息写回位置。
8. Agent 停止条件。
9. stdio MCP 子进程启动位置。

能够解释这九处代码，才算真正完成本练习。
