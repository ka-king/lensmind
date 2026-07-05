# Review #016 — Clarification Tool 返回值简化

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 已修改

---

## Before/After

| | Before | After |
|---|--------|-------|
| 返回值 | `f"[需要澄清] {question}"` | `question` |

## 影响范围

| 文件 | 影响 | 说明 |
|------|------|------|
| `tools/builtins/clarification_tool.py` | 🔄 一行 | 去前缀 |

---

## 问题

Tool 返回值带了 `"[需要澄清]"` 前缀，但这层语义是 middleware 的职责。
Tool 本身只负责"表达问题"，控制流由 ClarificationMiddleware 拦截。

## 决策

Tool 返回干净的 question 文本。格式化和暂停逻辑由 middleware 负责。

---

## 架构定位

```
ask_clarification tool  →  表达问题（纯数据）
ClarificationMiddleware  →  控制执行流（暂停/恢复）

Tool + Middleware 解耦 = 正确的分层
```
