# Review #011 — LocalSandbox 实现安全性

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 已修改

---

## Before/After

| | Before | After |
|---|--------|-------|
| 命令执行 | `shell=True` | `shlex.split()` + `shell=False` |
| 安全说明 | 无 | 明确标注"受控执行环境，非完全隔离 OS 沙箱" |

## 影响范围

| 文件 | 影响 | 说明 |
|------|------|------|
| `sandbox/local/local_sandbox.py` | 🔄 安全加固 | shell=True → shlex.split + shell=False |
| `tools/builtins/bash_tool.py` | 🔄 安全加固 | 同上 |

---

## 问题

`LocalSandbox` 使用 `subprocess.run(shell=True)` 执行命令：
- 命令注入攻击面
- 不受控的环境变量展开
- 进程在宿主机进程树中运行，没有真正的 OS 级隔离

## Review 意见

### 1. shell=True → shell=False + shlex.split（✅ 采纳）

低成本高收益的安全提升。`shlex.split()` 按 POSIX 规则拆分命令字符串，避免 shell 注入。

### 2. 明确沙箱定位（✅ 采纳）

在 docstring 中标注：这是受控执行环境，不是安全隔离系统。真正的进程隔离需要 Docker/E2B provider。

### 3. 不做 Docker/E2B 升级（✅ 延迟）

当前阶段不需要。等 sandbox interface contract 稳定后再切换 provider。

---

## 架构定位

```
Agent → Middleware → Sandbox → subprocess (host OS)

  当前:  controlled execution environment
  未来:  Docker/E2B → secure isolation boundary
```

---

## 修改文件

- `backend/packages/lensmind/sandbox/local/local_sandbox.py`
- `backend/packages/lensmind/tools/builtins/bash_tool.py`

## 测试结果

18/18 passed
