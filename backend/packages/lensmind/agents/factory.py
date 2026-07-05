"""纯参数 Agent 工厂——不读文件、不读环境变量。

位于 langchain.create_agent 底层原语 和 config.yaml 驱动工厂之间的
SDK 级入口。所有依赖通过参数传入。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware

from lensmind.agents.features import RuntimeFeatures

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.tools import BaseTool
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph.state import CompiledStateGraph

__author__ = "万"

logger = logging.getLogger(__name__)


def create_lensmind_agent(
    model: BaseChatModel,
    tools: list[BaseTool] | None = None,
    *,
    system_prompt: str | None = None,
    middleware: list[AgentMiddleware] | None = None,
    features: RuntimeFeatures | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    name: str = "lensmind",
) -> CompiledStateGraph:
    """纯参数创建 LensMind Agent——零文件 I/O。

    参数:
        model: 已配置好的 ChatModel 实例。
        tools: 用户提供的工具列表。
        system_prompt: 系统提示词。None 则用电商视频主编默认提示词。
        middleware: 完整接管中间件链（与 features 互斥）。
        features: 声明式功能开关，自动组装中间件链。
        checkpointer: LangGraph 状态持久化后端。
        name: Agent 名称，用于日志和子 Agent 命名。

    返回:
        编译后的 LangGraph StateGraph，可调用 .invoke() / .stream()。

    异常:
        ValueError: 同时指定 middleware 和 features 时抛出。
    """
    if middleware is not None and features is not None:
        raise ValueError("不能同时指定 'middleware'（完整接管）和 'features'。")

    effective_tools: list[BaseTool] = list(tools or [])

    if middleware is not None:
        effective_middleware = list(middleware)
    else:
        feat = features or RuntimeFeatures()
        effective_middleware = _assemble_from_features(feat)

    # 启用子 Agent 功能时自动注入 task_tool
    if features and features.subagent:
        from lensmind.tools.task_tool import task_tool
        if task_tool.name not in {t.name for t in effective_tools}:
            effective_tools.append(task_tool)

    # 始终注入澄清反问工具
    from lensmind.tools.builtins.clarification_tool import ask_clarification_tool
    effective_tools.append(ask_clarification_tool)

    if system_prompt is None:
        from lensmind.agents.lead_agent.prompt import LEAD_AGENT_SYSTEM_PROMPT
        system_prompt = LEAD_AGENT_SYSTEM_PROMPT

    logger.info(
        "create_lensmind_agent: model=%s, tools=%d, middleware=%d, name=%s",
        model.model_name if hasattr(model, 'model_name') else 'unknown',
        len(effective_tools), len(effective_middleware), name,
    )

    return create_agent(
        model=model,
        tools=effective_tools or None,
        middleware=effective_middleware,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        name=name,
    )


def _assemble_from_features(feat: RuntimeFeatures) -> list[AgentMiddleware]:
    """从 RuntimeFeatures 组装有序的中间件链。

    顺序（不可变）:
      0. SandboxMiddleware           — 沙箱隔离
      1. ToolErrorHandlingMiddleware  — 工具错误处理
      2. SubagentLimitMiddleware      — 子 Agent 并发限制
      3. LoopDetectionMiddleware      — 死循环检测
      4. ClarificationMiddleware      — 需求澄清（必须在最后）
    """
    chain: list[AgentMiddleware] = []

    # 沙箱中间件
    if feat.sandbox is not False:
        if isinstance(feat.sandbox, AgentMiddleware):
            chain.append(feat.sandbox)
        else:
            from lensmind.sandbox.middleware import SandboxMiddleware
            chain.append(SandboxMiddleware())

    # 工具错误处理（始终开启）
    from lensmind.middlewares.tool_error_handler import ToolErrorHandlingMiddleware
    chain.append(ToolErrorHandlingMiddleware())

    # 子 Agent 限制
    if feat.subagent is not False:
        from lensmind.middlewares.subagent_limiter import SubagentLimitMiddleware
        if isinstance(feat.subagent, AgentMiddleware):
            chain.append(feat.subagent)
        else:
            chain.append(SubagentLimitMiddleware())

    # 死循环检测
    if feat.loop_detection is not False:
        from lensmind.middlewares.loop_detection import LoopDetectionMiddleware
        if isinstance(feat.loop_detection, AgentMiddleware):
            chain.append(feat.loop_detection)
        else:
            chain.append(LoopDetectionMiddleware())

    # 澄清反问（必须在最后——after_model 反序时第一个拦截 ask_clarification）
    from lensmind.middlewares.clarification import ClarificationMiddleware
    chain.append(ClarificationMiddleware())

    return chain
