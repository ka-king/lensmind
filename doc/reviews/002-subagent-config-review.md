# Review #002 — SubagentConfig 两层架构

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 已修改

---

## Before/After

| | Before | After |
|---|--------|-------|
| SubagentOverride | 3 字段 (name, timeout, max_turns, model) | 8 字段 + apply_to_spec() |
| SubagentSpec | 不存在 | 新增（定义层） |
| SubagentsConfig | overrides dict 容器 | specs + overrides 两层 + resolve_spec() |
| SubagentRunConfig 合并逻辑 | 硬编码 _DEFAULTS + override | 三层合并: spec → override → 全局默认 |

## 影响范围

| 文件 | 影响 | 说明 |
|------|------|------|
| `config/app_config.py` | 🔄 重写 | SubagentSpec 新增, SubagentOverride 增强, SubagentsConfig 增强 |
| `subagents/config.py` | 🔄 重写 | for_subagent() 改为三层合并逻辑 |
| `config.yaml` | ⚠️ 需补齐 | 新增 specs 段 + 展示 override 用法 |
| `tests/test_config.py` | ✅ 新增 | +4 个测试用例 |
| `agents/lead_agent/agent.py` | ✅ 无影响 | 通过 task_tool → config 间接调用 |
| `subagents/builtins/*` | ✅ 无影响 | spec 定义在 config.yaml 或模块自身，不侵入代码 |

---

## 问题

SubagentOverride 只有 3 个字段（timeout, max_turns, model），缺乏：

1. **定义层** — 没有 SubagentSpec，无法描述一个 Agent 的身份和能力
2. **输入输出契约** — Agent 之间无法自动串联
3. **Override 边界模糊** — 哪些可以覆盖、哪些不能覆盖没有约束

## Review 意见

### 1. 必须补 SubagentSpec（定义层）

将"配置"和"定义"分离成两层：

- SubagentSpec = Agent 的身份证（role, schema, tools, 默认运行时参数）
- SubagentOverride = 运行时覆盖（timeout, model, temperature）

### 2. Override 不能改变 capability / schema / role

加约束：`apply_to_spec()` 只覆盖运行时字段，role 和 schema 不可被 override 修改。

### 3. SubagentsConfig 不是容器，是管理层

从单纯的 `dict[str, SubagentOverride]` 升级为：
- specs 层（定义）
- overrides 层（覆盖）
- resolve_spec()（合并）
- 全局默认值（global_timeout/global_model）

### 4. 不加入执行策略字段

MVP 阶段不加 `enable_memory`、`parallel_allowed`、`require_confirmation`——没有对应执行层代码，加了也用不上。等 Phase 3 执行引擎就位后再加。

### 5. 不加入 Workflow DAG、RuntimeContext

这两个属于运行时层，不属于配置层。`app_config.py` 的职责是"YAML → typed dataclass"，配置边界必须守住。

---

## 采用的方案

`config.yaml` 中的 subagents 结构：

```yaml
subagents:
  timeout_seconds: 1800      # 全局默认
  global_max_turns: 20
  global_max_retries: 3
  global_model: ""

  # 定义层
  specs:
    product_analyzer:
      role: 产品分析师
      input_schema: {...}
      output_schema: {...}
      tools: []
      default_timeout_seconds: 60

  # 覆盖层（只覆盖运行时参数）
  agents:
    script_writer:
      model: claude-opus-4-7
      temperature: 0.9
```

运行配置合并优先级：

```
SubagentSpec 默认值 → SubagentOverride 覆盖 → SubagentsConfig 全局默认
```

## 架构决策

**四层边界**：

| 层 | 属于 | Phase |
|------|------|------|
| Config Layer (ModelConfig, SubagentSpec, SubagentOverride) | `app_config.py` | ✅ Phase 2 |
| Graph Layer (Workflow DAG, AgentNode, Edge) | `workflow/` | ⏸️ Phase 3 |
| Runtime Layer (Executor, Context, Memory) | `runtime/` | ⏸️ Phase 4 |
| Control Layer (Routing, Cost, Fallback) | `control/` | ⏸️ Phase 5 |

**核心原则**：配置文件不负责执行，override 不改变能力定义，每个层有自己明确的模块边界。

---

## 修改文件

- `backend/packages/lensmind/config/app_config.py` — SubagentSpec 新增加, SubagentOverride 增强, SubagentsConfig 增强
- `backend/packages/lensmind/subagents/config.py` — for_subagent() 三层合并逻辑
- `config.yaml` — 新增 specs 段 + override 示例
- `tests/test_config.py` — 新增 4 个测试用例

## 测试结果

12/12 passed
