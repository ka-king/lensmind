# Review #014 — Subagent Prompt 资产化

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 已修改

---

## Before/After

| | Before | After |
|---|--------|-------|
| Prompt 位置 | 硬编码在 Python 三引号字符串中 | `builtins/prompts/<name>.md` 独立文件 |
| 子 Agent 文件 | Prompt + 工厂 + 注册耦合在一起 | 工厂 + 注册，prompt 从文件加载 |
| 非开发可参与 | ❌ 改文案要 diff Python | ✅ 直接编辑 Markdown |

## 影响范围

| 文件 | 影响 |
|------|------|
| `builtins/__init__.py` | 🔄 新增 `_load_prompt()` |
| `builtins/prompts/*.md` | ★ 6 个 prompt 文件 |
| `builtins/*.py` (6个) | 🔄 prompt → `_load_prompt(name)` |

---

## 问题

6 个子 Agent 的 prompt 硬编码在 Python 源文件中，嵌套在三引号字符串里：
- 改文案需要 diff Python 文件
- 非开发人员无法参与 prompt 迭代
- Prompt 和逻辑耦合，无法独立版本化

## Review 意见

### Prompt 资产化（✅ 采纳）

把 prompt 抽成独立的 Markdown 文件：

```
builtins/
├── prompts/
│   ├── product_analyzer.md
│   ├── script_writer.md
│   ├── model_image_artist.md
│   ├── scene_designer.md
│   ├── storyboard_animator.md
│   └── video_editor.md
├── __init__.py          ← _load_prompt(name)
├── product_analyzer.py  ← _load_prompt("product_analyzer")
├── script_writer.py
└── ...
```

加载逻辑: `_load_prompt()` 读 `builtins/prompts/<name>.md`

### 不做 YAML spec 拆分（✅ 延迟）

Prompt 的 schema 约束（input_schema / output_schema）在 SubagentSpec (config.yaml) 中已定义。当前阶段不另起一套 YAML 定义文件。

---

## 结论

> Prompt 成为独立资产，Python 文件只保留工厂 + 注册逻辑。
> 6 个子 Agent 统一使用 `_load_prompt(name)` 从 Markdown 文件加载。

## 修改文件

- `subagents/builtins/prompts/*.md` — 6 个新增
- `subagents/builtins/__init__.py` — `_load_prompt()` 新增
- `subagents/builtins/*.py` — 6 个 prompt 字符串替换为加载调用

## 测试结果

18/18 passed
