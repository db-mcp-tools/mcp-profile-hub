"""profile_hub —— 档案中枢：唯一数据落点的 MCP 外壳（档案 / 基线 / 审计 / 事故 / 知识包）。

业务判断全部留在本包；跨 MCP 通用能力来自 dbt-core / dbt-store / dbt-know，
MCP 运行时外壳来自 dbt-mcp-kit。本包不 import 任何其他 MCP。
"""

from profile_hub.server import MCP_NAME, TOOLS, main
__all__ = ["MCP_NAME", "TOOLS", "main"]

__version__ = "0.2.0"
