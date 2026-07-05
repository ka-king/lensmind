# RFC: Skill 系统设计

## 1. 目标

Skill 系统是 LensMind 的能力扩展机制。Skill 定义了"做什么"，子 Agent 负责"谁来做"。

## 2. 核心概念

```
skills/public/          ← 所有 Skill 的目录
    ├── product-analyzer/
    │   └── SKILL.md    ← Skill 的主文件
    ├── script-generator/
    │   └── SKILL.md
    └── ...
```

每个 Skill = 一个独立目录 + 一个 `SKILL.md`，无需写 Python 代码。

## 3. SKILL.md 格式（带 frontmatter）

```yaml
---
name: product-analyzer
description: AI 分析电商产品，提取卖点和视觉风格建议
version: 1.0.0
tags: [analysis, product]
requires: [llm]           # llm | image_gen | video_gen | tts
inputs:                   # 输入参数 schema
  product_name:
    type: str
    required: false
  product_images:
    type: list[str]
    required: false
outputs:                  # 输出 schema
  type: ProductAnalysis
  fields:
    product_name: str
    category: str
    selling_points: list[str]
---

# Product Analyzer

...（Prompt 正文）...
```

## 4. 系统架构

```
┌──────────────────────────────────┐
│ skills/catalog.py                │
│  SkillCatalog                    │
│  - scan(public_path)             │  ← 扫描 skills/public/
│  - scan(system_path)             │  ← 扫描 .agent/skills/
│  - get(name) → SkillDef          │
│  - list_all() → list[SkillDef]   │
└──────────┬───────────────────────┘
           │
┌──────────▼───────────────────────┐
│ skills/parser.py                 │
│  parse_skill(md_path) → SkillDef │  ← 解析 SKILL.md
│  - 提取 frontmatter              │
│  - 提取 prompt 正文              │
│  - 验证必填字段                  │
└──────────┬───────────────────────┘
           │
┌──────────▼───────────────────────┐
│ skills/loader.py                 │
│  SkillLoader                     │
│  - load(skill_def) → Skill       │  ← 动态加载
│  - 加载 prompt.py（可选）        │
│  - 加载 tools.py（可选）         │
│  - 编译为子 Agent 可用的格式     │
└──────────┬───────────────────────┘
           │
┌──────────▼───────────────────────┐
│ skills/permissions.py            │
│  SkillPermissions                │
│  - can_load(skill_def, context)  │  ← 权限检查
│  - system skills 只读            │
│  - public skills 可启用/禁用     │
└──────────────────────────────────┘
```

## 5. SkillDef 类型

```python
@dataclass
class SkillDef:
    name: str
    description: str
    version: str
    tags: list[str]
    requires: list[str]          # [llm, image_gen, video_gen, tts]
    inputs: dict[str, FieldDef]
    outputs: OutputDef
    prompt: str                  # SKILL.md 正文
    path: str                    # 目录路径
    kind: str                    # "public" | "system"
    enabled: bool = True
```

## 6. 扫描加载流程

```python
class SkillCatalog:
    def scan(self, root_path: str, kind: str = "public") -> None:
        """扫描目录下所有 SKILL.md"""
        for md_path in Path(root_path).rglob("SKILL.md"):
            skill_def = parse_skill(md_path)
            skill_def.kind = kind
            self._registry[skill_def.name] = skill_def

    def get(self, name: str) -> SkillDef | None:
        """按名称获取 Skill 定义"""
        return self._registry.get(name)

    def list_by_tag(self, tag: str) -> list[SkillDef]:
        """按标签过滤"""
        return [s for s in self._registry.values() if tag in s.tags]
```

## 7. Skill 与子 Agent 的关系

```python
# 子 Agent 创建时加载 Skill 作为 System Prompt
from lensmind.skills.catalog import get_catalog
from lensmind.skills.loader import SkillLoader

def create_product_analyzer_subagent(model):
    catalog = get_catalog()
    skill_def = catalog.get("product-analyzer")
    
    loader = SkillLoader()
    skill = loader.load(skill_def)  # 解析 prompt，加载 tools

    return create_agent(
        model=model,
        system_prompt=skill.prompt,      # 从 SKILL.md 正文
        tools=skill.get_tools(),          # 从 tools.py
        name=skill_def.name,
    )
```

## 8. 后续扩展

| 阶段 | 能力 |
|------|------|
| Phase 1 | 静态 SKILL.md 扫描 + prompt 注入 |
| Phase 2 | SKILL.md 热加载（无需重启） |
| Phase 3 | Skill 市场（在线下载安装） |
| Phase 4 | Skill 校验 + 沙箱测试 |
