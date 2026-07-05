"""电商视频生成 Pipeline — 6 节点 DAG。

product_analyzer
    ↓
script_writer
    ↓
┌──────────────┬──────────────────┐
│ model_image  │ scene_designer   │  ← 并行组
│ _artist      │                  │
└──────┬───────┴──────┬───────────┘
       ↓              ↓
storyboard_animator
       ↓
video_editor
"""

from __future__ import annotations

from lensmind.workflow.plan import WorkflowNode, WorkflowPlan

__author__ = "万"


def build_video_pipeline() -> WorkflowPlan:
    """构建电商视频生成的 DAG 计划。"""

    nodes = [
        WorkflowNode(
            name="product_analysis",
            subagent_type="product_analyzer",
            prompt_template="分析以下产品并提取卖点、目标人群和视觉风格:\n{product_context}",
            depends_on=[],
        ),
        WorkflowNode(
            name="script",
            subagent_type="script_writer",
            prompt_template="根据产品分析创作分镜脚本:\n{product_analysis}",
            depends_on=["product_analysis"],
        ),
        WorkflowNode(
            name="model_images",
            subagent_type="model_image_artist",
            prompt_template="根据分镜脚本生成模特展示图:\n{script}",
            depends_on=["script"],
            parallel_group="image_generation",
        ),
        WorkflowNode(
            name="scene_images",
            subagent_type="scene_designer",
            prompt_template="根据分镜脚本生成背景场景图:\n{script}",
            depends_on=["script"],
            parallel_group="image_generation",
        ),
        WorkflowNode(
            name="clips",
            subagent_type="storyboard_animator",
            prompt_template="根据分镜脚本、模特图和场景图生成视频片段:\n脚本: {script}\n模特图: {model_images}\n场景图: {scene_images}",
            depends_on=["model_images", "scene_images"],
        ),
        WorkflowNode(
            name="final_video",
            subagent_type="video_editor",
            prompt_template="合成最终视频:\n分镜片段: {clips}\n脚本: {script}",
            depends_on=["clips"],
        ),
    ]

    edges = [
        ("product_analysis", "script"),
        ("script", "model_images"),
        ("script", "scene_images"),
        ("model_images", "clips"),
        ("scene_images", "clips"),
        ("clips", "final_video"),
    ]

    return WorkflowPlan(
        name="电商视频生成 Pipeline",
        description="产品分析 → 剧本 → 模特图+场景图(并行) → 分镜片段 → 最终视频",
        nodes=nodes,
        edges=edges,
    )
