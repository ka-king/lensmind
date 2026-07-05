"""MCP Tool → LangChain Tool 转换。

将 MCP Server 暴露的工具包装为 langchain_core.tools.BaseTool，
Agent 可以直接调用。
"""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

from lensmind.mcp.client import MCPClient, MCPToolDef

__author__ = "万"

logger = logging.getLogger(__name__)


def mcp_tools_to_langchain(client: MCPClient) -> list:
    """将 MCP Client 的所有工具转为 LangChain Tool 列表。

    参数:
        client: 已连接的 MCPClient。

    返回:
        langchain_core.tools.BaseTool 列表。
    """
    tools = []
    for tdef in client.list_tools():
        lc_tool = _build_tool(client, tdef)
        tools.append(lc_tool)
    return tools


def _build_tool(client: MCPClient, tdef: MCPToolDef):
    """为单个 MCP 工具构建 LangChain Tool。"""

    @tool(tdef.name, description=tdef.description)
    def _mcp_wrapper(**kwargs) -> str:
        """调用 MCP Server 上的工具。"""
        try:
            return client.call_tool(tdef.name, kwargs)
        except Exception as e:
            return f"MCP tool '{tdef.name}' error: {e}"

    # 标记为 MCP 来源（后续中间件可据此做路由）
    _mcp_wrapper.metadata = {"mcp_server": client.name, "mcp_tool": tdef.name}
    return _mcp_wrapper
