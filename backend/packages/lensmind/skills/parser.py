"""SKILL.md 解析器——YAML frontmatter + Markdown 正文。

格式:
    ---
    name: product-video
    description: 电商产品视频生成
    version: 1.0.0
    pipeline:
      nodes:
        - name: analysis
          subagent: product_analyzer
    ---
    # 正文（prompt）
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from lensmind.skills.types import PipelineNodeDef, SkillDef

__author__ = "万"

# 匹配 YAML frontmatter: 开头三横线之间的内容
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_skill(path: str | Path) -> SkillDef:
    """解析单个 SKILL.md 文件为 SkillDef。

    参数:
        path: SKILL.md 文件路径。

    返回:
        SkillDef 实例。

    异常:
        FileNotFoundError: 文件不存在。
        ValueError: frontmatter 格式错误或缺少必填的 name 字段。
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"SKILL.md 不存在: {path}")

    content = path.read_text(encoding="utf-8")

    # 提取 frontmatter
    fm_match = _FRONTMATTER_RE.match(content)
    if fm_match is None:
        raise ValueError(f"{path}: 缺少 YAML frontmatter（文件必须以 --- 开头）")

    frontmatter = yaml.safe_load(fm_match.group(1)) or {}
    if "name" not in frontmatter:
        raise ValueError(f"{path}: frontmatter 中缺少必填的 'name' 字段")

    # 解析 pipeline 节点
    pipeline_nodes = _parse_pipeline(frontmatter.get("pipeline", {}))

    # 正文 = frontmatter 之后的内容
    prompt = content[fm_match.end():].strip()

    return SkillDef(
        name=frontmatter["name"],
        description=frontmatter.get("description", ""),
        version=str(frontmatter.get("version", "0.1.0")),
        pipeline_nodes=pipeline_nodes,
        requires=frontmatter.get("requires", []),
        tags=frontmatter.get("tags", []),
        prompt=prompt,
        source_path=str(path),
    )


def _parse_pipeline(pipeline_data: dict) -> list[PipelineNodeDef]:
    """解析 pipeline.nodes 为 PipelineNodeDef 列表。"""
    nodes_raw = pipeline_data.get("nodes", [])
    result = []
    for nd in nodes_raw:
        result.append(PipelineNodeDef(
            name=nd.get("name", ""),
            subagent=nd.get("subagent", ""),
            depends_on=nd.get("depends_on", []),
            parallel_group=nd.get("parallel_group", ""),
        ))
    return result
