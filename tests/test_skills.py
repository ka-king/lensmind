"""Skills 系统测试——parser + catalog + loader。"""

from __future__ import annotations

import tempfile
from pathlib import Path

from lensmind.skills.catalog import SkillCatalog
from lensmind.skills.loader import SkillLoader
from lensmind.skills.parser import parse_skill

__author__ = "万"


def _write_skill_md(dir_path: Path, name: str, content: str, frontmatter: str = "") -> Path:
    """在目录下写入一个 SKILL.md 文件。"""
    md = dir_path / name / "SKILL.md"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(frontmatter + "\n" + content, encoding="utf-8")
    return md


def test_parse_minimal_skill():
    """验证最小 SKILL.md 解析。"""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_skill_md(
            Path(tmp), "test-skill",
            content="# Test\nHello world.",
            frontmatter="---\nname: test-skill\ndescription: A test skill\nversion: 1.0\n---",
        )
        skill = parse_skill(path)

        assert skill.name == "test-skill"
        assert skill.description == "A test skill"
        assert skill.version == "1.0"
        assert "# Test" in skill.prompt
        assert "Hello world" in skill.prompt


def test_parse_with_pipeline():
    """验证带 pipeline 定义的 SKILL.md 解析。"""
    with tempfile.TemporaryDirectory() as tmp:
        fm = """---
name: product-video
description: 电商视频
pipeline:
  nodes:
    - name: analysis
      subagent: product_analyzer
      depends_on: []
    - name: render
      subagent: video_editor
      depends_on: [analysis]
      parallel_group: render_group
---
"""
        path = _write_skill_md(Path(tmp), "product-video", content="# Body", frontmatter=fm)
        skill = parse_skill(path)

        assert skill.name == "product-video"
        assert len(skill.pipeline_nodes) == 2
        assert skill.pipeline_nodes[0].name == "analysis"
        assert skill.pipeline_nodes[1].depends_on == ["analysis"]
        assert skill.pipeline_nodes[1].parallel_group == "render_group"


def test_parse_missing_frontmatter():
    """验证缺少 frontmatter 时抛出 ValueError。"""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_skill_md(Path(tmp), "bad", content="# No frontmatter")
        try:
            parse_skill(path)
            assert False, "应抛出 ValueError"
        except ValueError as e:
            assert "frontmatter" in str(e).lower() or "---" in str(e)


def test_parse_missing_name():
    """验证 frontmatter 缺 name 时抛出 ValueError。"""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_skill_md(
            Path(tmp), "bad", content="# No name",
            frontmatter="---\ndescription: x\n---",
        )
        try:
            parse_skill(path)
            assert False, "应抛出 ValueError"
        except ValueError as e:
            assert "name" in str(e).lower()


def test_catalog_scan():
    """验证 catalog 扫描多个路径。"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        pub = tmp / "public"
        sys = tmp / "system"
        _write_skill_md(pub, "public-skill", content="# Pub", frontmatter="---\nname: public-skill\n---")
        _write_skill_md(sys, "system-skill", content="# Sys", frontmatter="---\nname: system-skill\n---")

        catalog = SkillCatalog()
        catalog.scan(public_path=str(pub), system_path=str(sys))

        assert len(catalog) == 2
        assert catalog.get("public-skill") is not None
        assert catalog.get("system-skill") is not None
        assert catalog.get("public-skill").kind == "public"
        assert catalog.get("system-skill").kind == "system"


def test_catalog_get_pipeline():
    """验证 catalog.get_pipeline() 转为 WorkflowPlan。"""
    with tempfile.TemporaryDirectory() as tmp:
        _write_skill_md(
            Path(tmp), "test",
            content="# Test",
            frontmatter="""---
name: test
pipeline:
  nodes:
    - name: a
      subagent: product_analyzer
      depends_on: []
    - name: b
      subagent: script_writer
      depends_on: [a]
---
""",
        )
        catalog = SkillCatalog()
        catalog.scan(public_path=str(tmp), system_path=str(tmp))

        plan = catalog.get_pipeline("test")
        assert plan is not None
        assert len(plan.nodes) == 2
        assert plan.get_node("b").depends_on == ["a"]


def test_loader_build_prompt():
    """验证 loader 构建 prompt 并注入 context。"""
    with tempfile.TemporaryDirectory() as tmp:
        _write_skill_md(
            Path(tmp), "test",
            content="分析产品: {product_name}",
            frontmatter="---\nname: test\n---",
        )
        catalog = SkillCatalog()
        catalog.scan(public_path=str(tmp), system_path=str(tmp))
        loader = SkillLoader(catalog)

        prompt = loader.build_prompt("test", {"product_name": "连衣裙"})
        assert "连衣裙" in prompt
