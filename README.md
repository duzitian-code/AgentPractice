# Agent Practice：亲手写出一个 Agent

这个仓库的主要目标不是展示一个已经写好的 Agent，而是让你通过六个递进实验，亲手完成：

```text
Host
 |-- 加载 Skill
 `-- 运行 Agent <-> Model
          |
       MCP Client <-> MCP Server -> Tool
```

完成后，你将能从代码层面回答：

- Tool 和普通 Python 函数有什么区别？
- MCP 如何把 Tool 的类型提示变成模型可读的 JSON Schema？
- Skill 为什么能影响流程，却不能执行动作？
- Model 为什么不会自己调用函数？
- Agent 如何处理 `tool_calls`，执行工具，再把结果交回 Model？
- Host 如何把 Model、Skill、Agent 和 MCP Server 组装并投入运行？

## 从这里开始

1. 阅读 [`workshop/README.md`](workshop/README.md)。
2. 只修改 `workshop/starter/` 中的 TODO。
3. 每完成一关，运行对应 checkpoint。
4. 卡住时再对照 `workshop/solution/`。

```powershell
# 安装
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .

# 查看第一关当前为什么失败
.\.venv\Scripts\python.exe -m workshop.checkpoints --lab 1

# 查看最终系统中每一条 Model/MCP 消息
.\.venv\Scripts\python.exe -m workshop.solution.main
```

下载较慢时可使用清华镜像：

```powershell
.\.venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e .
```

## 目录

| 路径 | 用途 |
|---|---|
| `workshop/starter/` | 学员实际编写的六关 TODO |
| `workshop/solution/` | 相同接口的参考答案 |
| `workshop/checkpoints.py` | 每一关的自动验收 |
| `workshop/support.py` | 离线 Model 模拟器和基础类型，不需要修改 |
| `src/agent_practice/` | 更完整的参考应用，支持真实 OpenAI 兼容模型 |
| `docs/reference-app.md` | 完整参考应用的使用说明 |
| `.github/agents/` | Awesome Copilot 风格的 Custom Agent 配置示例 |

> **两个 “Agent” 不要混淆：** `workshop/starter/agent.py` 是你亲手实现的 Agent 运行时循环；`.github/agents/*.agent.md` 是由 GitHub Copilot Host 读取的 Custom Agent 配置。

详细课程、每关任务和运行时序见 [`workshop/README.md`](workshop/README.md)。
