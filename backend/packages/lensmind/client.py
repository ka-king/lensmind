"""LensMindClient — 唯一公开的 API 入口。

用法:
    from lensmind.client import LensMindClient

    # 方式 1：读 config.yaml
    client = LensMindClient()
    result = client.generate_video("法式碎花连衣裙", [...])

    # 方式 2：纯 SDK（无配置文件）
    client = LensMindClient(model=my_model, features=RuntimeFeatures(...))
    result = client.generate_video("法式碎花连衣裙", [...])

    # 方式 3：DAG pipeline（6 节点自动编排）
    client = LensMindClient()
    outputs = client.run_pipeline("法式碎花连衣裙")
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from lensmind.agents.features import RuntimeFeatures
from lensmind.agents.factory import create_lensmind_agent
from lensmind.config.app_config import AppConfig, load_app_config
from lensmind.models.factory import create_model

__author__ = "万"

logger = logging.getLogger(__name__)


class LensMindClient:
    """LensMind 视频生成智能体的公开 API 客户端。

    封装了配置加载、模型创建、Agent 编译的完整流程。
    用户只需调用 generate_video() 即可完成视频生成。
    """

    def __init__(
        self,
        *,
        config: AppConfig | None = None,
        model: BaseChatModel | None = None,
        tools: list[BaseTool] | None = None,
        features: RuntimeFeatures | None = None,
    ):
        """初始化 LensMind 客户端。

        参数:
            config: AppConfig 实例。None 则从 config.yaml 加载。
            model: 聊天模型实例。None 则用配置中的默认模型。
            tools: 额外工具。
            features: 运行时功能开关。None 则从配置构建。
        """
        if config is None:
            config = load_app_config()

        if model is None:
            model = create_model(config=config)

        if features is None:
            features = RuntimeFeatures.from_config(config.features)

        self._config = config
        self._model = model
        self._tools = tools or []
        self._features = features
        self._graph = create_lensmind_agent(
            model=model,
            tools=self._tools,
            features=features,
        )

    def generate_video(
        self,
        product_name: str,
        product_images: list[str] | None = None,
        *,
        requirements: str = "",
        style: str = "product_showcase",
        duration_sec: int = 30,
    ) -> dict[str, Any]:
        """生成电商产品视频。

        参数:
            product_name: 产品名称或描述。
            product_images: 产品图片本地路径列表。
            requirements: 额外要求（自然语言）。
            style: 视频风格，可选 marketing / social_media / tutorial / product_showcase。
            duration_sec: 目标视频时长（秒）。

        返回:
            dict，包含 status、final_video_path、script、execution_log 等字段。
        """
        input_text = (
            f"请为以下产品生成一个 {duration_sec} 秒的电商视频。\n"
            f"产品名称：{product_name}\n"
        )
        if product_images:
            input_text += f"产品图片：{', '.join(product_images)}\n"
        if requirements:
            input_text += f"额外要求：{requirements}\n"
        input_text += f"风格：{style}\n"

        result = self._graph.invoke({
            "messages": [("user", input_text)],
            "product_name": product_name,
            "product_images": product_images or [],
            "requirements": requirements,
            "style": style,
            "duration_sec": duration_sec,
        })

        return result

    def run_pipeline(self, product_name: str, product_images: list[str] | None = None) -> dict[str, Any]:
        """通过 DAG 工作流引擎执行完整的视频生成 pipeline。

        6 节点 DAG:
          product_analysis → script → model+scene(并行) → clips → final_video

        参数:
            product_name: 产品名称。
            product_images: 产品图片路径。

        返回:
            {node_name: output} 的字典。
        """
        from lensmind.workflow import WorkflowEngine, build_video_pipeline

        plan = build_video_pipeline()
        engine = WorkflowEngine(self._model)

        context_parts = [f"产品名称: {product_name}"]
        if product_images:
            context_parts.append(f"产品图片: {', '.join(product_images)}")
        initial_context = {"product_context": "\n".join(context_parts)}

        return engine.run(plan, initial_context)

    def chat(self, message: str) -> dict[str, Any]:
        """向 Agent 发送消息，获取回复。

        参数:
            message: 用户消息文本。

        返回:
            包含 LangGraph 状态（messages 等）的 dict。
        """
        return self._graph.invoke({
            "messages": [("user", message)],
        })
