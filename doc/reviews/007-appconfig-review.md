# Review #007 — AppConfig 内核收束

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 已修改

---

## Before/After

| | Before | After |
|---|--------|-------|
| models 类型 | `list[ModelConfig]` | `dict[str, ModelConfig]` |
| 查找复杂度 | O(n) | O(1) |
| lookup 方法 | 保留 | 保留（薄封装） |
| ConfigRegistry | 无 | 无（当前不需要） |

## 影响范围

| 文件 | 影响 | 说明 |
|------|------|------|
| `config/app_config.py` | 🔄 models -> dict | O(1) 查找 |
| `models/factory.py` | 🔄 适配 | `next(iter(models.values()))` |
| `tests/test_config.py` | 🔄 适配 | dict 访问语法 |

---

## 问题

AppConfig 结构是正确的，但有一个潜在风险：
- `models: list` 导致 O(n) 查找
- 未来如果做 model routing，列表遍历不可接受

## Review 争议点

| 议题 | 原建议 | 最终决策 |
|------|--------|---------|
| models -> dict | 改 | ✅ 改（O(1)，值得） |
| 移除 lookup 方法 | 移除 | ❌ 保留（薄封装，统一入口） |
| 加 ConfigRegistry | 加 | ❌ 不加（无 registry 行为，空壳抽象） |

## 决策理由

### models -> dict（✅ 改）
O(1) 查找，路由选模场景必要。

### 保留 lookup 方法（✅ 正确）
`get_model_config()` 一行代码，是统一访问入口。删除只会让 `config.models.get()` 四处散落。

### 不抽 ConfigRegistry（✅ 正确）
当前没有任何 registry 行为——没有 capability 过滤、没有 role 匹配、没有多来源合并。
YAGNI 原则：等真正需要时再抽象。

---

## 未来演化路径

```
AppConfig (纯数据层)        ← 当前
     ↓
ConfigRegistry (查询 + 过滤) ← 触发条件:
     │                         capability filtering (supports_tools, vision)
     │                         role-based agent matching
     │                         多来源配置合并
     ↓
ModelRouter (选择 + 降级)    ← 触发条件:
                               cost-based selection
                               fallback chain
                               动态模型切换
```

---

## 修改文件

- `backend/packages/lensmind/config/app_config.py` — models: list → dict
- `backend/packages/lensmind/models/factory.py` — 适配 dict 访问
- `tests/test_config.py` — 适配

## 测试结果

18/18 passed
