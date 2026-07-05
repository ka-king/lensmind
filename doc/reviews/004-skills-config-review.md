# Review #004 — SkillsConfig 边界决策

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 已修改

---

## Before/After

| | Before | After |
|---|--------|-------|
| 字段数 | 2 | 4 |
| 定位 | 路径配置 | 加载策略配置 |
| 热加载 | 无 | `enable_hot_reload` |
| 缓存 | 无 | `cache_enabled` |

## 影响范围

| 文件 | 影响 | 说明 |
|------|------|------|
| `config/app_config.py` | 🔄 加字段 | SkillsConfig +2 字段 |
| `config.yaml` | ⚠️ 需补齐 | enable_hot_reload, cache_enabled |
| `tests/test_config.py` | ✅ 新增 | +1 测试用例 |
| `skills/catalog.py` | ✅ 无影响 | 待 Phase 3 实现时消费这些字段 |
| `skills/parser.py` | ✅ 无影响 | 待 Phase 3 |
| `skills/loader.py` | ✅ 无影响 | 待 Phase 3 |

---

## Review 意见

SkillsConfig 当前只有两个路径字段（`public_path`、`system_path`），没有 Skill 能力注册机制。

### 表面问题

- Skill 被当作"文件目录"，不是"能力单元"
- 没有 SkillRegistry
- 路径 ≠ 执行单元

### 但是——不应现在改

#### 1. Skill 的定义不在 config 里

Skill 的 source of truth 是 `skills/public/<name>/SKILL.md` 的 frontmatter，不是 config dataclass。如果也放进 config，会导致三源定义（YAML + Python + Markdown）。

#### 2. 消费端未实现

catalog、parser、loader 三个模块都还是空壳。现在往 config 加字段 = 提前设计消费端，属于典型的设计倒置。

#### 3. Skill vs Subagent 是不同的体系

| | Subagent | Skill |
|---|----------|-------|
| 形态 | Python 代码 | Markdown 文档 |
| 位置 | `builtins/*.py` | `skills/public/*/SKILL.md` |
| 定义来源 | `config.yaml` specs | `SKILL.md` frontmatter |
| 注册方式 | `registry.py` | `catalog.py` |

两者不共用同一套配置模型。

---

## 架构决策

```
SkillsConfig 的职责:
  → discovery layer config（路径 + 扫描策略）
  → 不是 Skill system definition

Skill 系统的职责:
  → parser.py: 解析 SKILL.md
  → catalog.py: 扫描 + 索引
  → loader.py: 动态加载
  → 属于 Phase 3 实现
```

### 后续升级方向（Phase 3 时考虑）

```
SkillsConfig:
  + enable_hot_reload: bool       # 热加载（有 loader 后）
  + cache_enabled: bool            # 缓存（有 catalog 后）

SkillSpec（在 SKILL.md frontmatter 中定义，不用 Python dataclass）:
  name, description, version
  inputs, outputs
  requires: [llm | image_gen | video_gen | tts]

SkillRegistry:
  register(skill) / get(name) / list_by_tag(tag)
```

### 现在不加的原因

| 字段 | 不加的原因 |
|------|-----------|
| `enable_hot_reload` | loader 未实现 |
| `cache_enabled` | catalog 未实现 |
| `SkillSpec` (Python) | 已在 SKILL.md frontmatter，双源会不一致 |
| `SkillRegistry` | 属于 catalog 模块，不属于 config 层 |

---

## 结论

> SkillsConfig 保持现状不变——它是路径配置，不是技能系统本身。
> Skill 系统的实现在 Phase 3（parser + catalog + loader）统一推进。
> 本次 review 的核心价值是**守住分层边界**，不是增加功能。
