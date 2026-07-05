# Review #010 — Sandbox 执行隔离抽象层

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 已修改

---

## Before/After

| | Before | After |
|---|--------|-------|
| 标识符 | `id: str` → `@property id` | `sandbox_id: str` → `@property sandbox_id` |

## 影响范围

| 文件 | 影响 | 说明 |
|------|------|------|
| `sandbox/sandbox.py` | 🔄 重命名 | `id` → `sandbox_id` |
| `sandbox/local/local_sandbox.py` | 🔄 适配 | `id=` → `sandbox_id=` |

---

## 设计确认

`Sandbox + SandboxProvider` 是标准的执行隔离抽象层：

```
SandboxProvider        创建隔离环境（工厂）
     ↓
Sandbox                执行接口（ABC）
     ↓
  execute_command()    命令执行
  read/write/delete    文件 IO
  list_dir             目录操作
     ↓
CommandResult          returncode + stdout + stderr
```

### 三层职责

| 层 | 职责 | 类比 |
|---|------|------|
| Provider | 创建隔离环境 | Docker daemon |
| Sandbox | 运行时执行接口 | Container |
| CommandResult | IO 契约 | exit code |

### 命名修正

`id` 太泛，且与 Python built-in `id()` 重叠。改为 `sandbox_id` 语义更清晰。

### 接口定位

当前是 command-centric API（`execute_command(str)`），适合作业控制和 FFmpeg 调用。未来扩展非 Bash runtime（Python REPL、WASM、SQL sandbox）时可能需要结构化执行接口，但那是 Phase 3+。

---

## 结论

> 这是标准的 execution isolation abstraction layer，设计正确且接近 production 级接口。
> 当前改动仅一个命名修正，其余保持现状。

## 修改文件

- `backend/packages/lensmind/sandbox/sandbox.py` — `id` → `sandbox_id`
- `backend/packages/lensmind/sandbox/local/local_sandbox.py` — 适配

## 测试结果

18/18 passed
