"""MCP 客户端——连接外部 AI 服务（图片/视频/TTS）。

协议: Model Context Protocol (MCP)
传输: stdio（子进程通信），后续可扩 SSE/HTTP

用法:
    client = MCPClient("image-gen", command="uvx", args=["image-gen-mcp"])
    tools = client.list_tools()
    result = client.call_tool("generate_image", {"prompt": "..."})
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

__author__ = "万"

logger = logging.getLogger(__name__)


@dataclass
class MCPToolDef:
    """MCP 工具定义——从 MCP Server 发现的工具元数据。"""
    name: str
    description: str = ""
    parameters: dict = field(default_factory=dict)  # JSON Schema


@dataclass
class MCPServerConfig:
    """MCP Server 连接配置。"""
    name: str                           # 服务名
    command: str = ""                   # 启动命令
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    tool_call_timeout: int = 60         # 单次工具调用超时（秒）


class MCPClient:
    """MCP 客户端——管理与单个 MCP Server 的连接。

    MVP: stdio 传输。使用 mcp Python SDK 的 stdio_client。
    """

    def __init__(self, config: MCPServerConfig):
        self._config = config
        self._tools: dict[str, MCPToolDef] = {}
        self._connected = False

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self) -> list[MCPToolDef]:
        """启动 MCP Server 子进程并发现工具。

        返回: 发现的工具列表。
        """
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            params = StdioServerParameters(
                command=self._config.command,
                args=self._config.args,
                env=self._config.env,
            )

            # 创建 stdio 客户端，返回 (read, write) 流
            self._stdio_ctx = stdio_client(params)
            read, write = self._stdio_ctx.__enter__()

            # 创建会话
            self._session_ctx = ClientSession(read, write)
            self._session = self._session_ctx.__enter__()
            self._session.__aenter__ = lambda: None  # type: ignore  # MVP sync

            # 初始化握手
            import asyncio
            asyncio.get_event_loop().run_until_complete(self._session.initialize())

            # 发现工具
            tools_result = asyncio.get_event_loop().run_until_complete(
                self._session.list_tools()
            )
            self._tools = {}
            for t in tools_result.tools:
                self._tools[t.name] = MCPToolDef(
                    name=t.name,
                    description=getattr(t, 'description', ''),
                    parameters=getattr(t, 'inputSchema', {}),
                )
            self._connected = True
            logger.info("MCP '%s' 已连接: %d 个工具", self.name, len(self._tools))
            return list(self._tools.values())

        except ImportError:
            logger.warning("mcp SDK 未安装，MCP '%s' 以 mock 模式运行", self.name)
            self._connected = True
            return []
        except Exception as e:
            logger.error("MCP '%s' 连接失败: %s", self.name, e)
            self._connected = False
            return []

    def list_tools(self) -> list[MCPToolDef]:
        return list(self._tools.values())

    def call_tool(self, tool_name: str, arguments: dict) -> str:
        """调用 MCP 工具。

        返回: 工具执行结果的文本表示。
        """
        if not self._connected:
            raise RuntimeError(f"MCP '{self.name}' 未连接")

        try:
            from mcp import ClientSession
            import asyncio

            result = asyncio.get_event_loop().run_until_complete(
                self._session.call_tool(tool_name, arguments)
            )
            # 提取文本内容
            parts = []
            for content in getattr(result, 'content', []):
                if hasattr(content, 'text'):
                    parts.append(content.text)
            return "\n".join(parts) if parts else str(result)

        except ImportError:
            return f"[mock] MCP tool '{tool_name}' called with: {arguments}"
        except Exception as e:
            logger.error("MCP '%s' 工具 '%s' 调用失败: %s", self.name, tool_name, e)
            raise

    def disconnect(self) -> None:
        """关闭 MCP 连接。"""
        errs = []
        if hasattr(self, '_session_ctx'):
            try:
                self._session_ctx.__exit__(None, None, None)
            except Exception as e:
                errs.append(str(e))
        if hasattr(self, '_stdio_ctx'):
            try:
                self._stdio_ctx.__exit__(None, None, None)
            except Exception as e:
                errs.append(str(e))
        self._connected = False
        self._tools.clear()
        if errs:
            logger.warning("MCP '%s' 断开时有错误: %s", self.name, "; ".join(errs))
        else:
            logger.info("MCP '%s' 已断开", self.name)
