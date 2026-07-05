"""Lead Agent 工厂——电商视频主编。

创建 LensMind 主编排 Agent，负责:
- 读取 config.yaml 加载模型和配置
- 通过 features → FEATURE_MIDDLEWARE_MAP → 组装中间件链
- 注入子 Agent 委托工具 + 澄清反问工具
- 注入电商视频主编系统提示词

langgraph.json 中注册的入口函数。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain.agents import create_agent

from lensmind.agents.factory import _assemble_from_features, _inject_feature_tools
from lensmind.agents.features import RuntimeFeatures
from lensmind.agents.lead_agent.prompt import LEAD_AGENT_SYSTEM_PROMPT
from lensmind.config.app_config import AppConfig, load_app_config
from lensmind.models.factory import create_model

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.tools import BaseTool
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph.state import CompiledStateGraph

__author__ = "万"

logger = logging.getLogger(__name__)


def make_lead_agent(
    config: AppConfig | None = None,
    model: BaseChatModel | None = None,
    tools: list[BaseTool] | None = None,
    *,
    features: RuntimeFeatures | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """创建 LensMind 主编 Agent（电商视频主编）。

    langgraph.json 中注册的主入口。
    从 config.yaml 读取模型/工具/功能配置。

    参数:
        config: AppConfig 实例。None 则从 config.yaml 加载。
        model: 聊天模型。None 则从配置创建默认模型。
        tools: 额外工具。
        features: 运行时功能开关。None 则从配置构建。
        checkpointer: LangGraph 状态持久化后端（可选）。

    返回:
        编译后的 LangGraph StateGraph。
    """
    if config is None:
        config = load_app_config()

    if model is None:
        model = create_model(config=config)

    if features is None:
        features = RuntimeFeatures.from_config(config.features)

    # 通过共享的 _assemble_from_features 组装中间件链
    middleware = _assemble_from_features(features)
    # ModelContextMiddleware 插入最前面——让 tool 层能获取 model
    from lensmind.agents.model_context_middleware import ModelContextMiddleware
    middleware.insert(0, ModelContextMiddleware(model))

    # 收集工具
    agent_tools: list[BaseTool] = list(tools or [])
    _inject_feature_tools(features, agent_tools)

    from lensmind.tools.builtins.clarification_tool import ask_clarification
    agent_tools.append(ask_clarification)

    logger.info(
        "创建 Lead Agent — model=%s, middleware=%d, tools=%d",
        model.model_name if hasattr(model, 'model_name') else 'unknown',
        len(middleware), len(agent_tools),
    )

    return create_agent(
        model=model,
        tools=agent_tools or None,
        middleware=middleware,
        system_prompt=LEAD_AGENT_SYSTEM_PROMPT,
        checkpointer=checkpointer,
        name="lensmind_lead",
    )
