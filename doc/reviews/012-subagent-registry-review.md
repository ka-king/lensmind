# Review #012 — Subagent Registry 插件注册中心

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 保持现状（Phase 3 升级）

---

## 设计确认

`subagents/registry.py` 是 runtime extension registry（运行时扩展注册中心）：

```python
_registry: dict[str, SubagentFactory]    # name → (model) → CompiledStateGraph

register_subagent(name, factory)          # 注册
get_subagent_factory(name)                # 查找
list_subagents()                          # 列举
_register_builtins()                      # 启动时自注册所有内置子 Agent
```

### 当前设计的优势

- Factory pattern 正确——子 Agent 是 graph，不是 function
- Lazy import 自注册简洁——每个 `builtins/*.py` import 时自动 `register_subagent()`
- API 干净——3 个方法，最小化接口

### Phase 3 升级方向

| 当前 | Phase 3 | 触发条件 |
|------|---------|---------|
| 全局 `_registry: dict` | `create_registry()` 工厂 | 多 app context / 多租户 |
| import 自注册 | 显式 `register_all()` | 测试隔离 / 热加载 |
| 扁平命名 `script_writer` | namespace `video.script_writer` | 外部插件 / 版本管理 |

---

## 结论

> 这是标准的 runtime subagent plugin registry，设计正确。
> MVP 保持现状，Phase 3 升级。
