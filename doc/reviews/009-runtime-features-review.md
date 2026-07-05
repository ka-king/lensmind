# Review #009 — RuntimeFeatures 执行覆盖契约

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 保持现状（设计确认，无代码改动）

---

## 设计确认

`RuntimeFeatures` 是 config layer 和 runtime layer 之间的适配层。

```
FeaturesConfig (config layer, app_config.py)
     │  declarative, YAML, 4-layer grouped bool
     │
     ▼  from_config()
RuntimeFeatures (runtime adapter, agents/features.py)
     │  executable, 3-state resolution, AgentMiddleware override
     │
     ▼  _assemble_from_features()
middleware chain → CompiledStateGraph
```

### 三态模型（核心设计）

| 值 | 含义 | 使用场景 |
|---|------|---------|
| `True` | 使用内置默认中间件 | 正常模式 |
| `False` | 禁用该能力 | 轻量模式、测试、关闭未实现功能 |
| `AgentMiddleware` 实例 | 替换为自定义实现 | 自定义沙箱、自定义循环检测 |

这不是类型混用，而是 **execution resolution DSL**——功能声明 + 覆盖钩子。

### 命名决策

保持 `RuntimeFeatures`（不改名）:
- Config 层已有 `ExecutionFeatures`（sandbox/subagent 分组），是 YAML 配置
- `RuntimeFeatures` 是运行时适配层，职责不同
- 两个名字区分了"配置声明"和"运行时解析"

### 未来演化

当 feature 语义开始膨胀时（如 `memory = SemanticMemoryMiddleware()` vs `VectorMemoryMiddleware()`），会自然升级为 policy system。但这是 Phase 3+ 的事。

---

## 结论

> RuntimeFeatures 不是功能开关，而是执行系统的可插拔接口层。
> 当前设计正确，保持现状。
