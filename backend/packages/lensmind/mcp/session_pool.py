"""MCP 会话池——管理多个 MCP Server 连接。

启动时从 extensions_config.json 读取配置，批量连接所有 MCP Server。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from lensmind.mcp.client import MCPClient, MCPServerConfig, MCPToolDef

__author__ = "万"

logger = logging.getLogger(__name__)


class MCPSessionPool:
    """MCP 会话池——管理所有 MCP Server 连接。"""

    def __init__(self):
        self._clients: dict[str, MCPClient] = {}

    def load_from_config(self, config_path: str = "extensions_config.json") -> int:
        """从 extensions_config.json 加载并连接所有 MCP Server。

        返回: 成功连接的 Server 数量。
        """
        path = Path(config_path)
        if not path.exists():
            logger.info("未找到 %s，跳过 MCP 加载", config_path)
            return 0

        data = json.loads(path.read_text(encoding="utf-8"))
        servers = data.get("mcpServers", {})
        count = 0

        for name, cfg in servers.items():
            if not cfg.get("enabled", True):
                continue
            config = MCPServerConfig(
                name=name,
                command=cfg.get("command", ""),
                args=cfg.get("args", []),
                env=cfg.get("env", {}),
                tool_call_timeout=cfg.get("tool_call_timeout", 60),
            )
            client = MCPClient(config)
            client.connect()
            if client.connected:
                self._clients[name] = client
                count += 1

        logger.info("MCP 会话池就绪: %d 个 Server", count)
        return count

    def get_client(self, name: str) -> MCPClient | None:
        return self._clients.get(name)

    def get_all_tools(self) -> dict[str, list[MCPToolDef]]:
        """获取所有 MCP Server 的工具列表。"""
        return {name: c.list_tools() for name, c in self._clients.items()}

    def call_tool(self, server: str, tool: str, arguments: dict) -> str:
        """跨 Server 调用工具。"""
        client = self._clients.get(server)
        if client is None:
            raise ValueError(f"MCP Server '{server}' 未连接")
        return client.call_tool(tool, arguments)

    def disconnect_all(self) -> None:
        for client in self._clients.values():
            client.disconnect()
        self._clients.clear()

    def __len__(self) -> int:
        return len(self._clients)
