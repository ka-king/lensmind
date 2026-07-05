# Review #017 — Bash Tool 沙箱路径修复

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 已修改

---

## Before/After

| | Before | After |
|---|--------|-------|
| 执行路径 | `bash_tool → subprocess.run → OS` | `bash_tool → contextvar → Sandbox.execute_command` |
| SandboxMiddleware | 占位 pass | 创建/释放沙箱 |
| 安全抽象 | ❌ 被绕过 | ✅ 一致性 |

## 影响范围

| 文件 | 影响 |
|------|------|
| `sandbox/_context.py` | ★ 新增，contextvar 桥接 |
| `sandbox/middleware.py` | 🔄 从占位到完整实现 |
| `tools/builtins/bash_tool.py` | 🔄 subprocess.run → sandbox.execute_command |

## 问题

`bash_tool` 之前直接用 `subprocess.run()` 执行命令，完全绕过了 SandboxMiddleware 和 Sandbox 抽象层。导致：
- security_level 无效
- capabilities 无效
- 沙箱策略全部失效
- 系统存在两条执行路径

## 修正

### 1. contextvar 桥接

```python
# sandbox/_context.py
_current_sandbox: ContextVar[Sandbox | None]
set_current_sandbox(sandbox) / get_current_sandbox() / clear_current_sandbox()
```

Middleware → contextvar → Tool，不通过全局变量。

### 2. SandboxMiddleware 实现

```
before_agent → LocalSandboxProvider.create_sandbox() → set_current_sandbox()
after_agent  → clear_current_sandbox()
```

### 3. bash_tool 转发

```
get_current_sandbox() → sandbox.execute_command(command)
降级：sandbox=None 时 fallback 到 subprocess（开发环境）
```

## 架构一致性

```
Before:  bash_tool → subprocess → OS  （绕过了整个体系）

After:
  bash_tool → _context.get_current_sandbox()
     ↑
  SandboxMiddleware → Provider → LocalSandbox.execute_command()
```

---

## 结论

> 修复了 bash tool 绕过沙箱体系的问题，执行路径恢复一致。
> 通过 contextvar 桥接 middleware 和 tool，保持分离。

## 修改文件

- `sandbox/_context.py` — 新增
- `sandbox/middleware.py` — 完整实现
- `tools/builtins/bash_tool.py` — 转发到沙箱

## 测试结果

18/18 passed
