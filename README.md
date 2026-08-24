# Agent 最小练习

基础练习只回答一个问题：

> **Model 想调用 Tool 时，Agent、Skill 和 MCP 分别做什么？**

基础部分仍然只改 **3 个文件**，按顺序完成约 20 分钟，不需要 API Key。进阶部分演示如何让编辑器和 GitHub Copilot 直接加载同类 Agent；这部分需要登录 GitHub Copilot。

| 练习 | 目的 | 实际操作 |
|---|---|---|
| 1. Tool | 写出真正执行工作的代码 | 补 1 行 |
| 2. MCP | 让 Tool 可被发现和调用 | 加 1 个装饰器 |
| 3. Skill | 写出可复用的做事规则 | 写 8 行 Markdown |
| 4. Agent | 串起 Model 和 Tool | 补 3 处代码 |
| 5. 编辑器与插件 | 让 Copilot 直接加载 Agent | 配置项目 Agent，并安装示例插件 |

```text
Skill --提供做事规则--> Agent --messages + tools--> Model
                         ^            |
                         |         tool_call
                         |            v
                         +---- MCP ----+----> Tool
                         |
                         +-- 把 Tool 结果作为 role="tool" 再交给 Model
```

## 准备：安装依赖

**目的：** 只安装 MCP SDK。

在项目根目录运行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

下载较慢时：

```powershell
.\.venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

---

## 练习 1：写一个 Tool

**目的：** 理解 Tool 首先只是一个执行确定任务的普通函数，与 Model、Agent、MCP 都无关。

**文件：** `practice\tool_mcp.py`

**操作：**

找到 `TODO 1`，删除 `raise NotImplementedError(...)`，改成：

```python
return f"{city}：晴，25°C"
```

**运行：**

```powershell
.\.venv\Scripts\python.exe practice\tool_mcp.py tool
```

**预期结果：**

```text
上海：晴，25°C
```

**完成后必须理解：**

> Tool 是真正执行工作的代码；Model 不能因为“知道函数名”就自动执行它。

---

## 练习 2：把 Tool 暴露给 MCP

**目的：** 理解 MCP 不是 Tool，而是让外部程序统一发现和调用 Tool 的协议。

**文件：** 仍然是 `practice\tool_mcp.py`

**操作：**

在 `query_weather` 函数上方添加一行：

```python
@mcp.tool()
```

完成后应是：

```python
@mcp.tool()
def query_weather(city: str) -> str:
    """查询指定城市的天气。"""
    return get_weather(city)
```

**运行：**

```powershell
.\.venv\Scripts\python.exe practice\tool_mcp.py mcp
```

**预期结果：**

输出中应包含：

```text
"name": "query_weather"
"city"
MCP 返回： {"result":"上海：晴，25°C"}
```

**观察：**

- MCP 根据函数名得到 Tool 名称。
- MCP 根据 docstring 得到 Tool 描述。
- MCP 根据 `city: str` 自动生成参数 JSON Schema。
- MCP Client 用名字和 JSON 参数调用 Tool，不需要知道函数实现。

**完成后必须理解：**

> Tool 是能力；MCP 是发布、发现和调用这个能力的标准方式。

---

## 练习 3：写一个 Skill

**目的：** 理解 Skill 是给 Agent/Model 使用的可复用文字规则，不是可执行代码。

**文件：** `practice\SKILL.md`

**操作：**

把文件内容替换为：

```markdown
---
name: weather-assistant
description: 回答天气问题。用户询问某个城市天气时使用。
---

# Weather Assistant

1. 从用户问题中识别城市。
2. 必须调用 `query_weather`，不能猜测天气。
3. 根据 Tool 返回值，用一句中文回答。
```

**检查：**

```powershell
Get-Content practice\SKILL.md
```

文件中不应再出现 `TODO`。

**完成后必须理解：**

> Skill 只告诉 Agent“怎么做”；真正查询天气的仍然是 Tool。

---

## 练习 4：写 Agent 循环

**目的：** 理解 Agent 是协调者：调用 Model、执行 Model 请求的 Tool、再把结果交回 Model。

**文件：** `practice\agent.py`

只补三处代码。

### 操作 4.1：Agent 调用 Model

找到 `TODO 4A`，把：

```python
reply = None
```

改为：

```python
reply = await demo_model(messages, model_tools)
```

### 操作 4.2：Agent 执行 Tool

找到 `TODO 4B`，把：

```python
result = None
```

改为：

```python
result = await client.call_tool(call["name"], call["arguments"])
```

### 操作 4.3：Agent 把 Tool 结果交回 Model

删除 `TODO 4C` 下方的 `raise NotImplementedError(...)`，改成：

```python
messages.append(
    {
        "role": "tool",
        "name": call["name"],
        "content": json.dumps(
            result.structured_content,
            ensure_ascii=False,
        ),
    }
)
```

**运行：**

```powershell
.\.venv\Scripts\python.exe practice\agent.py
```

**预期过程：**

```text
第 1 次 Model 输入：system(Skill) + user(问题) + MCP tools
第 1 次 Model 输出：tool_call(query_weather)
Agent：通过 MCP 执行 query_weather
第 2 次 Model 输入：增加 assistant(tool_call) + tool(结果)
第 2 次 Model 输出：最终文本
```

最后应看到：

```text
[最终答案]
Model 根据 Tool 结果回答：上海：晴，25°C
```

**完成后必须理解：**

> Model 只返回 `tool_call`；Agent 才真正执行 Tool，并把结果以 `role="tool"` 再次发送给 Model。

---

## 进阶练习 5：让 Copilot 直接使用 Agent

**目的：** 理解两种发布方式：

1. **项目级 Agent**：把 `.agent.md` 放进仓库，打开该项目的编辑器就能使用。
2. **Agent Plugin**：把 Agent、Skill 和 MCP Server 打成一个可安装目录，Copilot CLI 和 VS Code 可以跨项目使用。

这两种方式是替代关系，不必同时配置。项目级 Agent 适合随仓库共享；Plugin 适合复用和分发。

### 5.1 在编辑器中配置项目级 Agent

本仓库已经提供：

```text
.github\agents\weather-workspace.agent.md
.vscode\mcp.json
```

`.github\agents\*.agent.md` 是 VS Code 和 JetBrains 共用的项目级 Agent 位置。Agent 文件的关键部分是：

```yaml
---
name: weather-workspace
description: 使用本仓库的天气 MCP 工具回答城市天气；当用户询问天气、气温或天气状况时使用。
tools:
  - weather-workspace/query_weather
user-invocable: true
disable-model-invocation: false
---
```

| 字段 | 作用 |
|---|---|
| `description` | 说明“能做什么、何时使用”，也是模型能否正确隐式调用的主要依据 |
| `tools` | Agent 可以使用的工具白名单；它只授权工具，不保证一定调用 |
| `user-invocable` | 是否允许用户从 Agent 选择器手动调用，默认 `true` |
| `disable-model-invocation` | 是否禁止模型自动委派给该 Agent，默认 `false` |

在 VS Code 中运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
code .
```

然后打开 Copilot Chat，从输入框下方的 **Agent 选择器**选择 `weather-workspace`，输入：

```text
上海天气怎么样？
```

`.vscode\mcp.json` 会启动本仓库提供的 stdio MCP Server。第一次调用时，按编辑器提示确认启动和工具权限。

在 JetBrains 中，打开 Copilot Chat，在 Agent 下拉菜单中选择 **Configure Agents... → Workspace**，即可看到 `.github\agents` 中的 Agent。JetBrains 不读取 `.vscode\mcp.json`，需要在其 MCP 设置中另外注册同一个 Python 命令；其 Custom Agents 当前仍可能标记为 Preview。

> 选择 Agent 不等于执行 Tool。Agent 先把可用工具交给 Model，Model 再产生 `tool_call`，最后由 Copilot 执行 MCP Tool。

### 5.2 把 Agent 打成 Copilot Plugin

本仓库的完整 Agent Plugins 1.0 示例位于：

```text
plugins\weather-assistant\
├── plugin.json
├── mcp.json
├── servers\
│   └── weather_mcp.py
├── skills\
│   └── weather-assistant\
│       └── SKILL.md
└── com.github.copilot\
    └── agents\
        └── weather-assistant.agent.md
```

各文件的职责：

| 文件 | Copilot 如何使用 |
|---|---|
| `plugin.json` | 声明插件名称、版本和 Agent Plugins 规范版本 |
| `mcp.json` | 注册名为 `weather` 的 stdio MCP Server |
| `servers\weather_mcp.py` | 真正执行 `query_weather` Tool；它是完成版示例，不依赖基础练习中的 TODO |
| `skills\...\SKILL.md` | 提供可被自动发现或显式调用的天气 Skill |
| `com.github.copilot\agents\...agent.md` | 提供可选择或自动委派的自定义 Agent |

Agent Plugins 1.0 使用固定目录发现组件：可移植的 Skill 放在 `skills\`，MCP 配置放在根目录 `mcp.json`，Copilot 专用 Agent 放在 `com.github.copilot\agents\`。不要把旧版 CLI 插件中的顶层 `agents`、`skills`、`mcpServers` 路径字段混入这个 `plugin.json`。

安装前先安装依赖，并确保执行 Copilot 的环境中，`python` 指向该虚拟环境：

```powershell
Set-Location D:\workspace\AgentPractice
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

copilot plugin install .\plugins\weather-assistant
copilot plugin list
copilot mcp get weather
```

交互使用时，运行 `copilot`，输入 `/agent` 并选择 `weather-assistant`。也可以直接运行：

```powershell
copilot --agent weather-assistant `
  --prompt "上海天气怎么样？" `
  --allow-tool='weather(query_weather)'
```

`--allow-tool` 只预先批准工具权限，不会强制 Model 调用该工具。插件的 `mcp.json` 使用 `command: "python"`，安装插件不会自动安装 Python 依赖；Copilot CLI 应在上述已激活虚拟环境的终端中运行。VS Code 使用插件版 MCP 时，也要确保其启动环境中的 `python` 已安装 `mcp>=2,<3`；5.1 的项目配置则直接使用本仓库的虚拟环境解释器。

安装后的插件会复制到 `%USERPROFILE%\.copilot\installed-plugins\`；修改源码后需要重新执行 `copilot plugin install`。VS Code 可以发现 Copilot CLI 安装缓存中的插件，必要时执行 **Developer: Reload Window**。JetBrains 尚无与此等价的官方插件缓存说明，优先使用 5.1 的项目级 Agent。

该示例需要支持 Agent Plugins 1.0 的 Copilot CLI（至少 1.0.74）和较新的 VS Code。Business 或 Enterprise 组织还必须允许 **MCP servers in Copilot**。

### 5.3 显式调用、隐式调用与渐进式披露

通常写作“**显式调用**”，不是界面意义上的“显示调用”。

| 概念 | 谁做决定 | 本例 |
|---|---|---|
| **显式调用** | 用户明确指定 Agent、Skill 或 Tool | 选择 `weather-assistant`、使用 `--agent`、输入 `/weather-assistant:weather-assistant`，或用 `#` 把天气 Tool 加入提示 |
| **隐式调用** | Model 根据名称、`description`、当前任务和可用工具自行选择 | 用户只问天气，Model 自动委派给天气 Agent、加载天气 Skill 或调用 `query_weather` |
| **渐进式披露** | 客户端按需逐层加载上下文 | 启动时只读 Skill 的名称和描述；命中后再读完整 `SKILL.md`；确有需要时才读 `references\`、`scripts\`、`assets\` |

三者不能混为一谈：

- 显式与隐式调用回答的是“**谁选择这个能力**”。
- 渐进式披露回答的是“**何时把多少内容放进上下文**”，目的是节省上下文，而不是执行能力。
- Agent Skill 正式定义了三层渐进式披露；Custom Agent 本身主要通过选择或委派加载，不应直接套用 Skill 的三层定义。
- MCP Tool 也可以通过 Tool Search 延迟加载定义，但“加载工具定义”仍不等于“执行工具”。

Agent 的调用方式可用两个字段控制：

| 配置 | 用户显式调用 | Model 隐式调用 |
|---|---:|---:|
| 两个字段都省略 | 是 | 是 |
| `user-invocable: false` | 否 | 是 |
| `disable-model-invocation: true` | 是 | 否 |
| 两者同时设置 | 否 | 否 |

插件中的描述特意同时写了“做什么”和“何时使用”，因为隐式调用主要依赖描述匹配。Plugin 来自外部时，应先检查其中的 MCP 程序和 Hooks；它们会以本机用户权限执行。

**官方资料：**

- [GitHub Copilot custom agents 配置](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- [VS Code Custom Agents](https://code.visualstudio.com/docs/agent-customization/custom-agents)
- [VS Code Agent Plugins](https://code.visualstudio.com/docs/agent-customization/agent-plugins)
- [Agent Plugins 1.0 Specification](https://agent-plugins.org/specification)
- [GitHub Copilot CLI 插件](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating)
- [Agent Skills 的渐进式披露](https://agentskills.io/specification#progressive-disclosure)

---

## 最后用七句话复述

完成练习后，请不看代码回答：

1. **Tool**：执行确定任务的函数。
2. **MCP**：让 Tool 可以被统一发现和调用的协议。
3. **Skill**：告诉 Agent/Model 如何完成某类任务的文字规则。
4. **Agent**：维护消息和循环，连接 Skill、Model 与 Tool。
5. **显式调用**：用户明确指定要使用哪个 Agent、Skill 或 Tool。
6. **隐式调用**：Model 根据描述和上下文自行选择能力。
7. **渐进式披露**：先加载少量元数据，命中后再按需加载完整说明和资源。

`practice\agent.py` 中的 `demo_model` 是一个固定行为的模型替身，因此无需 API Key。换成真实模型时，只替换 `demo_model`，Agent 循环、Skill、MCP 和 Tool 的关系不变。
