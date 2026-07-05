"""RuntimeFeatures — 声明式的 Agent 功能开关。

控制中间件链的组装。每个字段三种取值：
- True:  使用内置默认中间件
- False: 完全关闭该功能（不注入对应中间件）
- AgentMiddleware 实例: 替换为自定义中间件实现
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain.agents.middleware import AgentMiddleware

from lensmind.config.app_config import FeaturesConfig

__author__ = "万"


@dataclass
class RuntimeFeatures:
    """运行时功能开关——决定 Agent 中间件链的组成。"""

    sandbox: bool | AgentMiddleware = True
    """沙箱隔离。True 使用本地子进程沙箱，False 关闭隔离。"""

    memory: bool | AgentMiddleware = True
    """跨会话记忆。True 使用内置记忆中间件。"""

    summarization: bool | AgentMiddleware = False
    """长对话自动摘要。MVP 阶段默认关闭。"""

    subagent: bool | AgentMiddleware = True
    """子 Agent 委托。核心功能，必须开启。"""

    vision: bool | AgentMiddleware = True
    """图片视觉能力。允许 Agent 查看用户上传的产品图。"""

    auto_title: bool | AgentMiddleware = False
    """自动生成对话标题。MVP 阶段默认关闭。"""

    loop_detection: bool | AgentMiddleware = True
    """死循环检测。防止 Agent 陷入重复工具调用。"""

    guardrail: bool | AgentMiddleware = False
    """工具调用前的策略审查。MVP 阶段默认关闭。"""

    @classmethod
    def from_config(cls, config: FeaturesConfig) -> RuntimeFeatures:
        """从 YAML 配置构建 RuntimeFeatures。"""
        return cls(
            sandbox=config.sandbox,
            memory=config.memory,
            summarization=config.summarization,
            subagent=config.subagent,
            vision=config.vision,
            auto_title=config.auto_title,
            loop_detection=config.loop_detection,
            guardrail=config.guardrail,
        )
