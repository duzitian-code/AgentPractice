---
name: weather-assistant
description: 使用 weather MCP 的 query_weather 工具查询指定城市并用一句中文回答；当用户询问天气、气温或天气状况时使用。
---

# Weather Assistant

1. 从用户问题中识别城市；城市不明确时先询问用户。
2. 必须调用 `weather/query_weather`，不能猜测天气。
3. 根据 Tool 返回值，用一句简洁的中文回答。
