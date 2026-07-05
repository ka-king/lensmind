"""LensMindClient — 唯一公开的 API 入口。

架构: Skill → Lead Agent(Planner) → DAG Engine(Executor) → Subagents

用法:
    from lensmind.client import LensMindClient

    client = LensMindClient()
    result = client.generate_video("法式碎花连衣裙")     # DAG 执行
    reply  = client.chat("这件产品适合什么风格？")        # Lead Agent 对话
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
    """LensMind API 客户端。

    generate_video() — DAG Engine 确定性执行视频生成管线
    chat()           — Lead Agent 对话（需求澄清、风格建议等）
    """

    def __init__(
        self,
        *,
        config: AppConfig | None = None,
        model: BaseChatModel | None = None,
        tools: list[BaseTool] | None = None,
        features: RuntimeFeatures | None = None,
    ):
        if config is None:
            config = load_app_config()

        if model is None:
            model = create_model(config=config)

        if features is None:
            features = RuntimeFeatures.from_config(config.features)

        self._config = config
        self._model = model
        self._features = features
        self._graph = create_lensmind_agent(
            model=model,
            tools=tools,
            features=features,
        )

    # ---- 视频生成（DAG Engine 主导）----

    def generate_video(
        self,
        product_name: str,
        product_images: list[str] | None = None,
        *,
        requirements: str = "",
        style: str = "product_showcase",
        duration_sec: int = 30,
    ) -> dict[str, Any]:
        """生成电商产品视频——DAG Engine 确定性执行。

        管线: product_analysis → script → model+scene(并行) → clips → final_video

        参数:
            product_name: 产品名称或描述。
            product_images: 产品图片本地路径列表。
            requirements: 额外要求。
            style: marketing / social_media / tutorial / product_showcase。
            duration_sec: 目标视频时长。

        返回:
            {"status": str, "outputs": dict, "final_node": str}
        """
        from lensmind.skills import get_catalog
        from lensmind.workflow import WorkflowEngine

        context_parts = [f"产品名称: {product_name}"]
        if product_images:
            context_parts.append(f"产品图片: {', '.join(product_images)}")
        if requirements:
            context_parts.append(f"额外要求: {requirements}")
        context_parts.append(f"风格: {style}, 时长: {duration_sec}秒")
        initial_context = {"product_context": "\n".join(context_parts)}

        # 从 SkillCatalog 加载 pipeline 定义
        catalog = get_catalog()
        catalog.scan(
            public_path=self._config.skills.public_path,
            system_path=self._config.skills.system_path,
        )
        plan = catalog.get_pipeline("product-video")
        if plan is None:
            raise ValueError("Skill 'product-video' 未在 catalog 中找到或缺少 pipeline 定义")

        engine = WorkflowEngine(self._model)

        import time
        import uuid
        from lensmind.persistence import Task, TaskRepository
        from lensmind.runtime import save_checkpoint

        task_id = uuid.uuid4().hex[:12]
        task = Task(task_id=task_id, product_name=product_name, status="running")

        try:
            wf_result = engine.run(plan, initial_context)
            save_checkpoint(task_id, wf_result)

            task.status = wf_result.status
            task.node_outputs = {n: nr.output for n, nr in wf_result.nodes.items()}
            task.total_ms = int(wf_result.total_duration_ms)
            task.finished_at = time.time()
            TaskRepository().save(task)

            return {
                "task_id": task_id,
                "status": wf_result.status,
                "outputs": task.node_outputs,
                "final_node": wf_result.get_output("final_video"),
                "completed": wf_result.completed_count,
                "failed": wf_result.failed_count,
                "total_ms": task.total_ms,
            }
        except Exception as e:
            logger.exception("DAG 执行失败")
            return {
                "status": "failed",
                "outputs": {},
                "final_node": "",
                "completed": 0,
                "failed": 1,
                "error_message": str(e),
            }

    # ---- 对话（Lead Agent）----

    def chat(self, message: str) -> dict[str, Any]:
        """向 Lead Agent 发送消息。

        用于需求澄清、风格建议、开放式问答。
        不经过 DAG Engine——走 LangGraph 单 Agent 路径。

        参数:
            message: 用户消息。

        返回:
            LangGraph 状态 dict（含 messages）。
        """
        return self._graph.invoke({
            "messages": [("user", message)],
        })
