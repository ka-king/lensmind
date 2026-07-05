"""Skill 加载器——将 SkillDef 注入子 Agent 的 system prompt。

用法:
    loader = SkillLoader(catalog)
    prompt = loader.build_prompt("product-video", context={"product_name": "..."})
"""

from __future__ import annotations

from lensmind.skills.catalog import SkillCatalog
from lensmind.skills.types import SkillDef

__author__ = "万"


class SkillLoader:
    """从 SkillCatalog 加载 Skill，构建子 Agent 可用的 prompt。"""

    def __init__(self, catalog: SkillCatalog):
        self._catalog = catalog

    def get_skill(self, name: str) -> SkillDef | None:
        """获取 Skill 定义。"""
        return self._catalog.get(name)

    def build_prompt(self, name: str, context: dict[str, str] | None = None) -> str:
        """构建注入子 Agent 的 prompt。

        从 SKILL.md 正文读取，并可选地注入上下文变量。

        参数:
            name: Skill 名称。
            context: 上下文变量替换，如 {"product_name": "连衣裙"}。

        返回:
            格式化后的 prompt 文本。
        """
        skill = self._catalog.get(name)
        if skill is None:
            raise ValueError(f"Skill 未找到: {name}")

        prompt = skill.prompt
        if context:
            for key, value in context.items():
                prompt = prompt.replace(f"{{{key}}}", str(value))

        return prompt

    def build_dag_prompt(self, name: str, node_name: str, context: dict[str, str] | None = None) -> str:
        """为 pipeline 中的特定节点构建 prompt。

        参数:
            name: Skill 名称。
            node_name: 节点名（如 "script"）。
            context: 上下文变量。

        返回:
            节点对应的 prompt 文本。
        """
        skill = self._catalog.get(name)
        if skill is None:
            raise ValueError(f"Skill 未找到: {name}")

        # 每个节点的 prompt = Skill 正文 + 节点名标识
        base = skill.prompt
        node_context = f"[当前阶段: {node_name}]\n{base}"
        if context:
            for key, value in context.items():
                node_context = node_context.replace(f"{{{key}}}", str(value))

        return node_context
