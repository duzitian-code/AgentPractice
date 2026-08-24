# 完整参考应用：从 Model 到 MCP

这是一个可直接运行的 Python 教学项目。练习场景是：**让 Agent 为团队设计一场入门工作坊**。项目刻意不使用大型 Agent 框架，让每层边界都能在几十行代码里被看见。

默认的 `demo` 模型不需要 API Key；它是确定性的“模型替身”，用于稳定展示工具调用协议。完成基础练习后，可以切换到任何支持 OpenAI Chat Completions Tool Calling 的模型服务。

## 学习目标

完成练习后，学员应该能够：

1. 区分 Model、Agent、Skill、Tool、MCP 和 Host。
2. 追踪一次完整的 `Model -> Agent -> MCP -> Tool -> Model` 调用。
3. 新增一个 MCP Tool，并让 Agent 动态发现它。
4. 修改 Skill 来改变工作流，而不修改 Agent 循环。
5. 从本地 stdio 切换到可部署的 Streamable HTTP。

## 它们是什么关系

```text
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
```

| 模块 | 本项目中的职责 | 对应文件 |
|---|---|---|
| Model | 根据消息决定调用工具或给出答案 | `src/agent_practice/models.py` |
| Agent | 组装上下文、限制循环、校验工具、回传结果 | `src/agent_practice/agent.py` |
| Skill | 用自然语言固化特定任务的步骤和边界 | `skills/workshop-planner/SKILL.md` |
| Tool | 执行可验证的议程设计和预算计算 | `src/agent_practice/mcp_server.py` |
| MCP | 让工具可被发现、描述和跨进程调用 | `src/agent_practice/mcp_tools.py` |
| Host | 启动 Agent/MCP Client 并呈现结果 | `src/agent_practice/cli.py` |

关键区别：

- **Model 不是 Agent**：模型只返回文本或工具调用意图，Agent 才执行循环。
- **MCP 不是 Tool**：Tool 是能力，MCP 是暴露和调用能力的标准协议。
- **Skill 不是代码插件**：Skill 主要是可移植的说明和资源；Agent 决定何时加载它。
- **MCP 不只提供 Tool**：本服务还暴露了 Resource 和 Prompt，可通过 `inspect` 观察。

## 1. 安装

需要 Python 3.11+。在 PowerShell 中运行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
```

如果已有虚拟环境但没有 pip：

```powershell
.\.venv\Scripts\python.exe -m ensurepip --upgrade
```

默认 PyPI 下载较慢时，可临时使用清华镜像：

```powershell
.\.venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e .
```

## 2. 先观察，不改代码

显示概念关系：

```powershell
.\.venv\Scripts\agent-practice.exe concepts
```

让 MCP Client 通过 **stdio 启动一个真实子进程**，完成握手并发现能力：

```powershell
.\.venv\Scripts\agent-practice.exe inspect --schemas
```

运行完整 Agent 循环：

```powershell
.\.venv\Scripts\agent-practice.exe run --trace
```

`--trace` 中应看到三轮模型调用：

```text
Model 请求 design_workshop_agenda
Agent 通过 MCP 调用 Tool
Model 请求 estimate_workshop_cost
Agent 通过 MCP 调用 Tool
Model 根据两个 Tool 结果生成最终答案
```

尝试改变输入，观察参数如何进入工具：

```powershell
.\.venv\Scripts\agent-practice.exe run "为 20 位有经验的开发者设计 120 分钟工作坊，预算 1500 元" --trace
```

## 3. 动手练习

建议用 60～90 分钟完成。

### 练习 A：解释边界

打开 `src/agent_practice/agent.py`，找到以下四个位置：

1. Skill 被放入 system message。
2. MCP 返回的 Tool schema 被转换成模型可识别的 function schema。
3. 模型请求的工具名被 MCP 发现结果约束。
4. Tool 结果以 `role=tool` 放回消息，然后再次调用模型。

检查问题：如果删除 Agent 循环，Model 能否自己执行 Python 函数？为什么？

### 练习 B：只改 Skill

编辑 `skills/workshop-planner/SKILL.md`，要求最终答案增加“风险与保障”小节，再次运行命令。

检查问题：为什么 Skill 可以改变做事流程，却没有新增系统能力？

> `demo` 模型为了保证离线结果可复现，只实现了固定输出模板。要观察自然语言 Skill 对生成结果的影响，请完成练习 D，切换真实模型。

### 练习 C：新增 MCP Tool

在 `src/agent_practice/mcp_server.py` 中新增：

```python
@mcp.tool()
def check_equipment(participants: int, laptops: int) -> dict[str, object]:
    """检查动手练习的电脑是否充足。"""
    ...
```

然后：

1. 在 `tests/test_mcp_server.py` 添加成功和不足两个测试。
2. 运行 `inspect --schemas`，确认不改 MCP Client 就能发现新工具。
3. 在 Skill 中要求使用新工具。
4. 使用真实模型观察它是否按需要选择该工具。

检查问题：新增 Tool 时，为什么 Agent 的通用循环不需要增加 `if tool_name == ...`？

### 练习 D：换成真实模型

不要把密钥写入代码或提交到仓库。`.env.example` 只展示变量名；本项目直接读取进程环境变量。

```powershell
$env:OPENAI_API_KEY = "your-key"
$env:OPENAI_MODEL = "your-tool-calling-model"
$env:OPENAI_BASE_URL = "https://api.openai.com/v1"
.\.venv\Scripts\agent-practice.exe run --provider openai --trace
```

对于兼容 OpenAI Chat Completions 的内部网关，只需修改 `OPENAI_BASE_URL`。模型必须支持 `tools` / `tool_calls`。

检查问题：换模型后，哪些层保持不变？哪些行为可能变化？

## 4. 从开发到投入使用

本地桌面 Host 通常使用 stdio；服务化部署使用 Streamable HTTP。启动 MCP HTTP 服务：

```powershell
.\.venv\Scripts\agent-practice-mcp.exe --transport streamable-http --port 8000
```

在另一个终端连接同一个 Agent：

```powershell
.\.venv\Scripts\agent-practice.exe inspect --mcp-url http://127.0.0.1:8000/mcp
.\.venv\Scripts\agent-practice.exe run --mcp-url http://127.0.0.1:8000/mcp --trace
```

协议和 Tool 没有变化，只有 transport 从子进程 stdio 变成了 HTTP。这正是 MCP 解耦 Host 与能力提供方的价值。

投入真实环境前还应补齐：

- 身份认证、Tool 最小权限和高风险操作人工确认。
- 超时、重试、速率限制、调用成本与审计日志。
- Prompt injection 防护；Tool 返回值只能视为不可信数据。
- 固定评测集、质量指标和失败回退策略。
- HTTP 层 TLS、网络边界、健康检查与版本兼容策略。

## 5. 在 GitHub Copilot 中使用

项目参考了 [awesome-copilot](https://github.com/github/awesome-copilot) 的文件化组织方式：

- `skills/workshop-planner/SKILL.md` 遵循 [Agent Skills 规范](https://agentskills.io/specification)。
- `.github/agents/agent-lab-coach.agent.md` 是一个 Custom Agent 教练。
- `.vscode/mcp.json` 注册本地 MCP Server，VS Code 可以启动并发现它。

先完成安装，再在 VS Code 中启用 `agent-practice` MCP Server。若虚拟环境不在项目的 `.venv`，需要同步修改 `.vscode/mcp.json` 中的 Python 路径。

## 6. 测试

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

测试分别覆盖 Skill 格式、MCP 契约、预算/议程 Tool，以及完整 Agent 工具循环。测试使用 MCP 的内存 transport，运行应用时则使用 stdio 或 Streamable HTTP。

## 推荐阅读顺序

1. `skills/workshop-planner/SKILL.md`
2. `src/agent_practice/mcp_server.py`
3. `src/agent_practice/mcp_tools.py`
4. `src/agent_practice/agent.py`
5. `src/agent_practice/models.py`
6. `src/agent_practice/cli.py`

参考资料：

- [Awesome GitHub Copilot](https://github.com/github/awesome-copilot)
- [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Agent Skills Specification](https://agentskills.io/specification)
