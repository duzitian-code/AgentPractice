from __future__ import annotations

from mcp.server import MCPServer


mcp = MCPServer("weather-server")


def get_weather(city: str) -> str:
    """Return deterministic sample weather for the tutorial."""
    normalized_city = city.strip()
    if not normalized_city:
        raise ValueError("city 不能为空")
    return f"{normalized_city}：晴，25°C"


@mcp.tool()
def query_weather(city: str) -> str:
    """查询指定城市的教学示例天气。"""
    return get_weather(city)


if __name__ == "__main__":
    mcp.run(transport="stdio")
