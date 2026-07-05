"""Skill 系统——SKILL.md 发现、解析、加载。

SKILL.md 是 Skill 的唯一定义来源（single source of truth）：
- frontmatter: name, description, pipeline, version, tags
- body: prompt（子Agent 系统提示词素材）

模块:
- parser.py: 解析 SKILL.md → SkillDef
- catalog.py: 扫描 + 索引所有 Skill
- loader.py: 加载 + 注入 context
- types.py: SkillDef / PipelineNodeDef
"""

from lensmind.skills.catalog import SkillCatalog, get_catalog
from lensmind.skills.loader import SkillLoader
from lensmind.skills.parser import parse_skill
from lensmind.skills.types import SkillDef

__author__ = "万"

__all__ = ["SkillCatalog", "SkillLoader", "SkillDef", "parse_skill", "get_catalog"]
