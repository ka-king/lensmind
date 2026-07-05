"""L2 集成测试——SKILL.md → WorkflowPlan 完整链路。"""

from __future__ import annotations

from lensmind.skills import SkillCatalog, SkillDef

__author__ = "万"


def test_product_video_skill_to_workflow():
    """验证 product-video SKILL.md 完整链路。"""
    catalog = SkillCatalog()
    catalog.scan(public_path="skills/public/", system_path=".agent/skills/")

    skill = catalog.get("product-video")
    assert skill is not None, "product-video Skill 应在 system path 中被发现"
    assert skill.kind == "system"
    assert len(skill.pipeline_nodes) == 6

    plan = skill.to_workflow_plan()
    assert plan.name == "product-video"
    assert len(plan.nodes) == 6
    assert plan.validate() == []

    # 验证依赖关系——script 依赖 product_analysis
    script = plan.get_node("script")
    assert "product_analysis" in script.depends_on

    # 验证并行组——model_images 和 scene_images 同组
    model = plan.get_node("model_images")
    scene = plan.get_node("scene_images")
    assert model.parallel_group == "image_generation"
    assert scene.parallel_group == "image_generation"

    # 验证汇合点——clips 依赖 model_images 和 scene_images
    clips = plan.get_node("clips")
    assert "model_images" in clips.depends_on
    assert "scene_images" in clips.depends_on


def test_public_skills_all_parseable():
    """验证 skills/public/ 下所有 SKILL.md 可正确解析。"""
    catalog = SkillCatalog()
    catalog.scan(public_path="skills/public/", system_path=".agent/skills/")

    public_skills = catalog.list_public()
    assert len(public_skills) == 6

    expected = {
        "product-analyzer", "script-writer",
        "model-image-artist", "scene-designer",
        "storyboard-animator", "video-editor",
    }
    found = {s.name for s in public_skills}
    assert found == expected, f"公开 Skill 不匹配: {found}"


def test_catalog_get_nonexistent_returns_none():
    """验证不存在的 Skill 返回 None。"""
    catalog = SkillCatalog()
    catalog.scan()
    assert catalog.get("nonexistent-skill-xyz") is None
    assert catalog.get_pipeline("nonexistent") is None
