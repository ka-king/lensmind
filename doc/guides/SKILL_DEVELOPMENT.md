# Skill 开发指南

## 1. 什么是 Skill

Skill 是 LensMind 的可插拔能力单元。每个 Skill 是一个独立目录，包含一个 `SKILL.md` 文件，定义了该 Skill 的角色、输入、输出和行为。

## 2. Skill 目录结构

```
skills/public/product-analyzer/
├── SKILL.md              # ★ 核心：Skill 定义（必须）
├── prompt.py             # 附加：Prompt 模板（可选）
├── tools.py              # 附加：专有工具（可选）
└── examples/             # 附加：示例（可选）
    └── sample_output.json
```

## 3. SKILL.md 格式

```markdown
---
name: product-analyzer
description: 分析电商产品，提取卖点、受众和视觉风格
version: 1.0.0
author: lensmind
tags: [analysis, product]
requires: [llm]
---

# Product Analyzer

## 角色
你是一个专业的电商产品分析师。

## 任务
分析用户提供的产品信息（名称+图片），输出结构化的产品分析结果。

## 输入
- `product_name` (str): 产品名称
- `product_images` (list[str]): 产品图片路径列表

## 输出
```json
{
  "product_name": "string",
  "category": "string",
  "selling_points": ["string"],
  "target_audience": "string",
  "visual_style": "string",
  "tone": "string"
}
```

## 约束
- selling_points 至少 3 个
- visual_style 从 ["法式浪漫", "简约北欧", "日系清新", "美式复古", "科技未来"] 中选择
- tone 从 ["活泼亲切", "专业权威", "温柔叙事", "激情带货"] 中选择
```

## 4. Skill 生命周期

```
                      ┌──────────────┐
    创建 SKILL.md ───→│ skills/      │
                      │ public/      │
                      └──────┬───────┘
                             │
                    catalog.scan()  ← 启动时扫描
                             │
                             ▼
                      ┌──────────────┐
                      │ catalog.py   │ ← 解析 SKILL.md
                      │ 注册到 Registry│
                      └──────┬───────┘
                             │
                    Agent 触发 skill
                             │
                             ▼
                      ┌──────────────┐
                      │ loader.py    │ ← 动态加载 prompt/tools
                      └──────────────┘
```

## 5. 开发新 Skill

### Step 1: 创建目录

```bash
mkdir -p skills/public/my-new-skill
```

### Step 2: 写 SKILL.md

定义角色、输入输出、约束。

### Step 3: 测试

```python
from lensmind.skills.catalog import SkillCatalog
from lensmind.skills.parser import parse_skill

catalog = SkillCatalog()
catalog.scan("skills/public/")

skill_def = catalog.get("my-new-skill")
print(skill_def.name, skill_def.description)
```

### Step 4: 注册到 config.yaml

```yaml
skills:
  public_path: skills/public/
```

Skill 即被自动发现和加载。

## 6. Skill vs 子 Agent

| | Skill | 子 Agent |
|---|---|---|
| 是什么 | 一个能力描述（SKILL.md） | 一个独立的 Agent 实例 |
| 定义方式 | Markdown 文档 | Python 代码 + Prompt |
| 谁使用 | 子 Agent 加载 Skill 获取能力 | Lead Agent 委托任务给子 Agent |
| 例子 | `product-analyzer/SKILL.md` | `builtins/product_analyzer.py` |
| 关系 | Skill 定义"做什么" | 子 Agent 是"谁来做" |
