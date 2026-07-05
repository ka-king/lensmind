"""纯参数 Agent 工厂——零文件 I/O 的执行图编译器。

位于 langchain.create_agent 底层原语和 config.yaml 驱动工厂之间的 SDK 级入口。
所有依赖通过参数注入，不读文件、不读环境变量。

核心职责:
  RuntimeFeatures → FEATURE_MIDDLEWARE_MAP → middleware chain → create_agent()
  即: 功能声明 → 中间件映射 → 有序执行链 → 编译后的 Agent 图
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware

from lensmind.agents.features import RuntimeFeatures
from lensmind.middlewares.clarification import ClarificationMiddleware
from lensmind.middlewares.loop_detection import LoopDetectionMiddleware
from lensmind.middlewares.subagent_limiter import SubagentLimitMiddleware
from lensmind.middlewares.tool_error_handler import ToolErrorHandlingMiddleware
from lensmind.sandbox.middleware import SandboxMiddleware

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.tools import BaseTool
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph.state import CompiledStateGraph

__author__ = "万"

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature → Middleware 映射表
# ---------------------------------------------------------------------------

# 执行顺序即列表顺序——每个条目定义了:
#   feature_name: RuntimeFeatures 上的属性名
#   middleware_cls: 默认中间件类
#   always_on: True 则该中间件无论 feature 值如何都会被注入
FEATURE_MIDDLEWARE_MAP: list[dict] = [
    {"feature": "sandbox",        "class": SandboxMiddleware,           "always": False},
    {"feature": None,              "class": ToolErrorHandlingMiddleware,  "always": True},
    {"feature": "subagent",       "class": SubagentLimitMiddleware,      "always": False},
    {"feature": "loop_detection",  "class": LoopDetectionMiddleware,      "always": False},
    {"feature": None,              "class": ClarificationMiddleware,      "always": True,
     "note": "必须在最后——after_model 反序时第一个拦截 ask_clarification"},
]

# 与 feature 绑定的额外工具——feature 开启时自动注入
FEATURE_TOOL_MAP: dict[str, str] = {
    "subagent": "lensmind.tools.task_tool:task_tool",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


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

    middleware 和 features 二选一:
    - middleware: 完整接管中间件链，适合需要精确控制顺序的场景
    - features: 声明式开关，通过 FEATURE_MIDDLEWARE_MAP 自动组装

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
    """
    if middleware is not None and features is not None:
        raise ValueError("不能同时指定 'middleware'（完整接管）和 'features'。")

    effective_tools: list[BaseTool] = list(tools or [])

    if middleware is not None:
        effective_middleware = list(middleware)
    else:
        feat = features or RuntimeFeatures()
        effective_middleware = _assemble_from_features(feat)

    # Feature 绑定的工具自动注入
    if features:
        _inject_feature_tools(features, effective_tools)

    # 始终注入澄清反问工具
    from lensmind.tools.builtins.clarification_tool import ask_clarification
    effective_tools.append(ask_clarification)

    if system_prompt is None:
        from lensmind.agents.lead_agent.prompt import LEAD_AGENT_SYSTEM_PROMPT
        system_prompt = LEAD_AGENT_SYSTEM_PROMPT

    logger.info(
        "create_lensmind_agent: model=%s, tools=%d, middleware=%d, name=%s",
        model.model_name if hasattr(model, 'model_name') else 'unknown',
        len(effective_tools), len(effective_middleware), name,
    )

    # ModelContextMiddleware 插入最前面——让 tool 层能获取 model
    from lensmind.agents.model_context_middleware import ModelContextMiddleware
    effective_middleware.insert(0, ModelContextMiddleware(model))

    return create_agent(
        model=model,
        tools=effective_tools or None,
        middleware=effective_middleware,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        name=name,
    )


# ---------------------------------------------------------------------------
# Internal: middleware assembly + tool injection
# ---------------------------------------------------------------------------


def _assemble_from_features(feat: RuntimeFeatures) -> list[AgentMiddleware]:
    """从 RuntimeFeatures 按 FEATURE_MIDDLEWARE_MAP 组装中间件链。

    遍历映射表:
    - always_on → 无条件注入默认中间件
    - feature=True → 注入默认中间件
    - feature 是 AgentMiddleware 实例 → 注入自定义实现（替换默认）
    - feature=False → 跳过
    """
    chain: list[AgentMiddleware] = []

    for entry in FEATURE_MIDDLEWARE_MAP:
        feature_name = entry["feature"]
        middleware_cls = entry["class"]
        always_on = entry["always"]

        if always_on:
            chain.append(middleware_cls())
        elif feature_name is not None:
            feature_value = getattr(feat, feature_name)
            if feature_value is False:
                continue
            if isinstance(feature_value, AgentMiddleware):
                chain.append(feature_value)
            else:
                chain.append(middleware_cls())

    return chain


def _inject_feature_tools(feat: RuntimeFeatures, tools: list[BaseTool]) -> None:
    """根据 feature 开关注入绑定的工具。"""
    import importlib

    for feature_name, tool_path in FEATURE_TOOL_MAP.items():
        feature_value = getattr(feat, feature_name)
        if feature_value is False:
            continue
        # 反射加载工具
        module_path, tool_name = tool_path.split(":")
        module = importlib.import_module(module_path)
        tool_obj = getattr(module, tool_name)
        if tool_obj.name not in {t.name for t in tools}:
            tools.append(tool_obj)
