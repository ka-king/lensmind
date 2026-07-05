"""Skill 目录——扫描、索引、查找 SKILL.md。

启动时扫描 skills/public/ 和 .agent/skills/，
解析所有 SKILL.md 文件，建立 name → SkillDef 索引。
"""

from __future__ import annotations

import logging
from pathlib import Path

from lensmind.skills.parser import parse_skill
from lensmind.skills.types import SkillDef

__author__ = "万"

logger = logging.getLogger(__name__)


class SkillCatalog:
    """Skill 目录——所有已安装 Skill 的注册表。

    用法:
        catalog = SkillCatalog()
        catalog.scan(public_path="skills/public/", system_path=".agent/skills/")
        skill = catalog.get("product-video")
        pipeline = catalog.get_pipeline("product-video")
    """

    def __init__(self):
        self._skills: dict[str, SkillDef] = {}

    # ---- 扫描 ----

    def scan(self, public_path: str = "skills/public/", system_path: str = ".agent/skills/") -> int:
        """扫描 public 和 system 路径下的所有 SKILL.md。

        返回: 发现的 Skill 数量。
        """
        count = 0
        count += self._scan_path(Path(public_path), kind="public")
        count += self._scan_path(Path(system_path), kind="system")
        logger.info("Skill 目录扫描完成: %d 个 Skill (public=%d, system=%d)",
                     len(self._skills),
                     sum(1 for s in self._skills.values() if s.kind == "public"),
                     sum(1 for s in self._skills.values() if s.kind == "system"))
        return count

    def _scan_path(self, root: Path, kind: str) -> int:
        """递归扫描目录下的 SKILL.md 文件。"""
        if not root.exists():
            return 0
        count = 0
        for md_path in root.rglob("SKILL.md"):
            try:
                skill = parse_skill(md_path)
                skill.kind = kind
                if skill.name in self._skills:
                    logger.warning("Skill 名冲突: '%s' 已存在，%s 被跳过",
                                   skill.name, md_path)
                    continue
                self._skills[skill.name] = skill
                count += 1
                logger.debug("发现 Skill: %s (%s)", skill.name, md_path)
            except Exception as e:
                logger.error("解析 SKILL.md 失败 (%s): %s", md_path, e)
        return count

    # ---- 查询 ----

    def get(self, name: str) -> SkillDef | None:
        """按名称获取 Skill。"""
        return self._skills.get(name)

    def list_all(self) -> list[SkillDef]:
        """列出所有 Skill。"""
        return list(self._skills.values())

    def list_public(self) -> list[SkillDef]:
        """列出所有公开 Skill。"""
        return [s for s in self._skills.values() if s.kind == "public"]

    def list_system(self) -> list[SkillDef]:
        """列出所有系统 Skill。"""
        return [s for s in self._skills.values() if s.kind == "system"]

    def get_pipeline(self, name: str):
        """获取 Skill 的 pipeline 定义（转为 WorkflowPlan）。"""
        skill = self.get(name)
        if skill is None or not skill.pipeline_nodes:
            return None
        return skill.to_workflow_plan()

    def __len__(self) -> int:
        return len(self._skills)

    def __contains__(self, name: str) -> bool:
        return name in self._skills


# 全局单例
_catalog: SkillCatalog | None = None


def get_catalog() -> SkillCatalog:
    """获取全局 Skill 目录单例。"""
    global _catalog
    if _catalog is None:
        _catalog = SkillCatalog()
    return _catalog
