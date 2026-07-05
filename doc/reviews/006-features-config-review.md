# Review #006 — FeaturesConfig 分层分组

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 已修改

---

## Before/After

| | Before | After |
|---|--------|-------|
| 结构 | 8 个 flat bool | 4 个嵌套 dataclass，每层 2 个字段 |
| 类型安全 | ✔ bool | ✔ 强类型分组，IDE 补全 |
| 语义 | 散沙 | 按子系统分层 |
| 向后兼容 | — | 同时支持分组和扁平 YAML |

## 影响范围

| 文件 | 影响 | 说明 |
|------|------|------|
| `config/app_config.py` | 🔄 重写 | +4 个子 dataclass，FeaturesConfig 重组 |
| `agents/features.py` | 🔄 更新 | from_config() 改用嵌套访问 |
| `config.yaml` | ⚠️ 需补齐 | 默认写分组格式，扁平也可解析 |
| `tests/test_config.py` | ✅ 重写 | 2 个测试 -> features，移除旧扁平测试 |
| `agents/lead_agent/agent.py` | ✅ 无影响 | 通过 RuntimeFeatures.from_config() 消费 |
| `agents/factory.py` | ✅ 无影响 | 同上 |

---

## 问题

FeaturesConfig 8 个 flat bool 混在一起，控制 4 个不同子系统：
- 执行层 (sandbox, subagent)
- 记忆层 (memory, summarization)
- 安全层 (guardrail, loop_detection)
- UX 层 (vision, auto_title)

一个上帝开关面板，没有分组语义。

## Review 意见

### 1. 拆成嵌套 dataclass

不使用 dict 分组（丢类型安全），不使用 FeatureFlag(level/config) 过度抽象（无消费端）。

用 4 个独立 dataclass，每层有自己的类型。

### 2. 保持 bool

中间件消费者只读 True/False。level 字符串 / config dict 没有对应执行代码，属于过早抽象。

### 3. 不做 policy engine

当前阶段是 feature gating，不是 feature policy system。Phase 3 执行引擎就位后再考虑升级。

---

## 采用的方案

```python
ExecutionFeatures   sandbox, subagent
MemoryFeatures      memory, summarization
SafetyFeatures      guardrail, loop_detection
UXFeatures          vision, auto_title

FeaturesConfig
  execution: ExecutionFeatures
  memory: MemoryFeatures
  safety: SafetyFeatures
  ux: UXFeatures
```

YAML 两种写法都支持：

```yaml
# 推荐：分组
features:
  execution: {sandbox: true, subagent: true}
  memory: {memory: true, summarization: false}

# 兼容：扁平
features:
  sandbox: true
  subagent: true
  memory: true
```

## 架构决策

```
MVP (flat bool) → 当前 (嵌套 dataclass) → Phase 3 (policy engine)

现在: typed feature gating config (工业标准)
不做: policy-driven feature system (过早)
```

---

## 修改文件

- `backend/packages/lensmind/config/app_config.py` — 4 子 dataclass + FeaturesConfig 重组
- `backend/packages/lensmind/agents/features.py` — from_config() 改用嵌套访问
- `config.yaml` — 分组格式
- `tests/test_config.py` — 测试重写

## 测试结果

18/18 passed
