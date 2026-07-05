"""MCP (Model Context Protocol) 客户端——外部 AI 服务统一接入层。

client/         MCPClient（连接管理 + 工具发现 + 调用）
session_pool/   MCPSessionPool（多 Server 会话复用）
tools/          MCP Tool → LangChain Tool 转换
"""

from lensmind.mcp.client import MCPClient, MCPServerConfig, MCPToolDef
from lensmind.mcp.session_pool import MCPSessionPool
from lensmind.mcp.tools import mcp_tools_to_langchain

__author__ = "万"

__all__ = [
    "MCPClient", "MCPServerConfig", "MCPToolDef",
    "MCPSessionPool", "mcp_tools_to_langchain",
]
