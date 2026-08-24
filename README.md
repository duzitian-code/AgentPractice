# Agent 最小练习

本练习只回答一个问题：

> **Model 想调用 Tool 时，Agent、Skill 和 MCP 分别做什么？**

总共只改 **3 个文件**，按顺序完成约 20 分钟，不需要 API Key。

| 练习 | 目的 | 实际操作 |
|---|---|---|
| 1. Tool | 写出真正执行工作的代码 | 补 1 行 |
| 2. MCP | 让 Tool 可被发现和调用 | 加 1 个装饰器 |
| 3. Skill | 写出可复用的做事规则 | 写 8 行 Markdown |
| 4. Agent | 串起 Model 和 Tool | 补 3 处代码 |

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

## 最后用四句话复述

完成练习后，请不看代码回答：

1. **Tool**：执行确定任务的函数。
2. **MCP**：让 Tool 可以被统一发现和调用的协议。
3. **Skill**：告诉 Agent/Model 如何完成某类任务的文字规则。
4. **Agent**：维护消息和循环，连接 Skill、Model 与 Tool。

`practice\agent.py` 中的 `demo_model` 是一个固定行为的模型替身，因此无需 API Key。换成真实模型时，只替换 `demo_model`，Agent 循环、Skill、MCP 和 Tool 的关系不变。
