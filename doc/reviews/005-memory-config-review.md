# Review #005 — MemoryConfig 策略层升级

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 已修改

---

## Before/After

| | Before | After |
|---|--------|-------|
| 字段数 | 3 | 5 |
| 定位 | 存储控制 | 记忆系统策略层 |
| 自动提取 | 无 | `auto_extract` |
| 自动更新 | 无 | `auto_update` |

## 影响范围

| 文件 | 影响 | 说明 |
|------|------|------|
| `config/app_config.py` | 🔄 加字段 | MemoryConfig +2 字段 |
| `config.yaml` | ⚠️ 需补齐 | auto_extract, auto_update |
| `tests/test_config.py` | ✅ 新增 | +1 测试用例 |
| `agents/middlewares/memory.py` | ✅ 无影响 | 中间件占位，待 Phase 4 |
| `persistence/models/` | ✅ 无影响 | MemoryFact 运行时模型待 Phase 4 |

---

## 问题

MemoryConfig 只有 3 个字段（enabled、max_facts、max_injection_tokens），是"存储控制"，不是"记忆系统策略"。

## Review 意见

### 1. 缺乏结构

Memory 现在是平铺的 fact 列表，没有重要性评分、时间衰减、类型分类。

### 2. 缺乏注入策略

只有 max_injection_tokens 一个截断参数，没有排序策略、过滤阈值。

### 3. MemoryFact 和 MemoryStrategy

完整系统需要结构化的事实模型和检索排序策略。

---

## 采用的方案

MemoryConfig 加 2 个策略开关：

```python
@dataclass
class MemoryConfig:
    enabled: bool = True
    max_facts: int = 50
    max_injection_tokens: int = 2000
    auto_extract: bool = True     # ← 新增
    auto_update: bool = True      # ← 新增
```

### 现在不加的

| 不加 | 原因 |
|------|------|
| `MemoryFact` (importance/decay/type) | 运行时数据模型，属于 `persistence/models/` |
| `MemoryStrategy` (ranking/filter/inject_top_k) | 检索排序是 runtime 行为，不属于 config 层 |
| `ranking_strategy` / `filter_threshold` | 等 Phase 4 记忆引擎实现后启用 |

### 职责边界

```
MemoryConfig:         "要不要记"(enabled) + "记多少"(max_facts/tokens) + "自动吗"(auto_extract/update)
Memory 引擎(Phase 4): "怎么检索" + "怎么排序" + "怎么注入"
MemoryFact(Phase 4):  运行时数据模型，在 persistence/models/ 中定义
```

---

## 修改文件

- `backend/packages/lensmind/config/app_config.py` — MemoryConfig +2 字段
- `config.yaml` — auto_extract, auto_update
- `tests/test_config.py` — +1 测试用例

## 测试结果

17/17 passed
