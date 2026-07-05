# Review #013 — SubagentRunConfig 策略解析引擎

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 已修改（docstring 升级）

---

## Before/After

| | Before | After |
|---|--------|-------|
| 定位 | "运行配置" | "policy resolution engine" |
| 代码 | 不变 | 不变 |

## 影响范围

| 文件 | 影响 | 说明 |
|------|------|------|
| `subagents/config.py` | 🔄 docstring | 定位升级 |
| 其余 | ✅ 无 | 代码不变 |

---

## 设计确认

`SubagentRunConfig.for_subagent()` 本质是 **policy resolution engine**：

```
spec 默认值 → config.yaml override → 全局 fallback
     能力定义          用户调优              系统兜底
```

三层优先级语义不同：
- spec: 子 Agent 固有能力边界
- override: 部署环境调优
- fallback: 系统安全兜底

## 决策

### 不抽 `SubagentConfigResolver`（✅ 延迟）

当前只有一个 `for_subagent()` 方法，逻辑清晰、代码量小。抽成独立 service = 薄壳包装，没有实质收益。等需要第二个 resolution 逻辑时再拆。

### 不升级为 strategy system（✅ 延迟）

`ResolutionStrategy` (SPEC_FIRST / OVERRIDE_FIRST / COST_OPTIMIZED) 是 Phase 3+ 的事。当前一个 merge 规则够用。

---

## 结论

> SubagentRunConfig 已从配置对象升级为策略解析引擎。
> 当前代码不变，docstring 升级以反映真实定位。
