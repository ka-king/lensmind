# Review #018 — Task Tool 执行闭环

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 已修改

---

## Before/After

| | Before | After |
|---|--------|-------|
| 调度 | ✅ 查找 factory + 构建 config | ✅ 同上 |
| 执行 | ❌ `return f"[{name}] 任务已接收..."` | ✅ `executor.execute_subagent()` |
| 数据流 | dispatch → mock string | dispatch → executor → graph.invoke() → 真实输出 |

## 影响范围

| 文件 | 影响 |
|------|------|
| `subagents/executor.py` | ★ 新增，子 Agent 执行器 |
| `agents/_context.py` | ★ 新增，model contextvar |
| `agents/model_context_middleware.py` | ★ 新增，注入 model |
| `tools/task_tool.py` | 🔄 mock → executor |
| `agents/factory.py` | 🔄 注入 ModelContextMiddleware |
| `agents/lead_agent/agent.py` | 🔄 注入 ModelContextMiddleware |

## 问题

`task_tool` 只做 dispatch 不做 execute——查找子 Agent 后返回 mock 字符串。
系统是"半闭环"：有调度接口，没有执行引擎。

## 修正

### 三层分离

```
task_tool        → dispatch (查找 factory + 构建 config)
executor         → execute  (创建 graph + invoke)
model_context    → inject   (model 通过 contextvar 传递)
```

### 执行链路

```
Lead Agent → task_tool
               │
               ├── registry.get_subagent_factory(name)
               ├── SubagentRunConfig.for_subagent(name, config)
               │
               └── executor.execute_subagent(type, prompt, context, model)
                       │
                       ├── factory(model) → CompiledStateGraph
                       └── graph.invoke({"messages": [...]})
                            └── 提取 AI 消息 → return output
```

### Model 注入

```
ModelContextMiddleware (before_agent)
  → contextvar.set(model)
       ↓
  task_tool → get_current_model()
       ↓
  executor → factory(model) → invoke
```

---

## 结论

> task_tool 从"假编排"进入"真实执行闭环"。
> 调度层 (task_tool) 和执行层 (executor) 分离。
> Model 通过 contextvar 注入，不污染全局状态。

## 修改文件

- `subagents/executor.py` — 新增
- `agents/_context.py` — 新增
- `agents/model_context_middleware.py` — 新增
- `tools/task_tool.py` — mock → executor
- `agents/factory.py` — ModelContextMiddleware 注入
- `agents/lead_agent/agent.py` — 同上

## 测试结果

18/18 passed
