# Review #008 — Agent Factory 执行图编译器

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 已修改

---

## Before/After

| | Before | After |
|---|--------|-------|
| feature→middleware | 隐式 if-else 链 | `FEATURE_MIDDLEWARE_MAP` 显式映射表 |
| tool injection | 硬编码 if in factory | `FEATURE_TOOL_MAP` 反射加载 |
| lead_agent 复用 | 自己写一份 `_build_middlewares` | 复用 `_assemble_from_features` |
| 可测试性 | ❌ 映射逻辑藏在 if 里 | ✅ 映射表可独立测试 |

## 影响范围

| 文件 | 影响 | 说明 |
|------|------|------|
| `agents/factory.py` | 🔄 重写 | FEATURE_MIDDLEWARE_MAP + _assemble_from_features |
| `agents/lead_agent/agent.py` | 🔄 简化 | 复用 factory 的 _assemble_from_features |

---

## 问题

`_assemble_from_features` 中 feature → middleware 的映射是隐式的 if-else 链：
- 无法直接看出哪个 feature 对应哪个 middleware
- 中间件顺序藏在代码逻辑中
- 两个文件各自写了一份组装逻辑

## Review 意见

### 1. 加 FEATURE_MIDDLEWARE_MAP（✅ 采纳）

把隐式 if-else 改成显式映射表：

```python
FEATURE_MIDDLEWARE_MAP = [
    {"feature": "sandbox",        "class": SandboxMiddleware,           "always": False},
    {"feature": None,              "class": ToolErrorHandlingMiddleware,  "always": True},
    {"feature": "subagent",       "class": SubagentLimitMiddleware,      "always": False},
    {"feature": "loop_detection",  "class": LoopDetectionMiddleware,      "always": False},
    {"feature": None,              "class": ClarificationMiddleware,      "always": True},
]
```

好处: 映射关系一眼可见、顺序明确、可测试。

### 2. lead_agent 复用 _assemble_from_features（✅ 采纳）

原来 `lead_agent/agent.py` 自己写了一份 `_build_middlewares`，重复了一样的 if-else 逻辑。改为直接 import 复用。

### 3. 保留 `bool | AgentMiddleware` 多态（✅ 保留）

Feature 字段支持三种值的设计保留:
- True → 内置默认
- False → 跳过
- AgentMiddleware 实例 → 自定义替换

这是可扩展性的关键——用户可以注入自定义沙箱/循环检测实现。去掉会失去灵活性。

### 4. 不做 PipelineSpec（✅ 当前不需要）

Middleware 顺序固化在 FEATURE_MIDDLEWARE_MAP 的列表顺序中，当前阶段够用。等需要"不同 Agent 不同 pipeline"或"插件化中间件"时再升级。

---

## 架构决策

```
create_lensmind_agent() = 执行图编译器（Execution Graph Compiler）

职责:
  RuntimeFeatures → FEATURE_MIDDLEWARE_MAP → middleware chain → CompiledStateGraph
  功能声明 → 映射表查找 → 有序执行链 → 编译后的 Agent 图
```

不是简单的工厂函数，而是从声明式配置到运行时图结构的编译过程。

---

## 修改文件

- `backend/packages/lensmind/agents/factory.py` — FEATURE_MIDDLEWARE_MAP + _inject_feature_tools
- `backend/packages/lensmind/agents/lead_agent/agent.py` — 复用 _assemble_from_features

## 测试结果

18/18 passed
