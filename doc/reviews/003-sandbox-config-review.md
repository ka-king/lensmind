# Review #003 — SandboxConfig 安全执行边界升级

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 已修改

---

## Before/After

| | Before | After |
|---|--------|-------|
| 字段数 | 4 | 5 + SandboxCapabilities 嵌套 |
| 安全模型 | `allow_host_bash: bool`（二值开关） | `security_level: int`（0-3 分级） |
| 能力声明 | 无 | `SandboxCapabilities`（bash/python/file_system/network/subprocess） |
| Tool routing | ❌ 无法判断沙箱能力 | ✅ 可基于 capabilities 做 routing |

## 影响范围

| 文件 | 影响 | 说明 |
|------|------|------|
| `config/app_config.py` | 🔄 重写 | SandboxCapabilities 新增, SandboxConfig 增强 |
| `config.yaml` | ⚠️ 需补齐 | 新增 security_level + capabilities 段 |
| `tests/test_config.py` | ✅ 新增 | +4 测试用例 |
| `sandbox/sandbox.py` | ✅ 无影响 | 抽象基类不变 |
| `sandbox/local/local_sandbox.py` | ✅ 无影响 | 沙箱实现不变 |

---

## 问题

SandboxConfig 现在是"限制参数集合"，不是"安全执行模型"：
- `allow_host_bash: bool` 太粗，无法表达分级信任
- 系统不知道沙箱能做什么——无法做 tool routing 和 agent-sandbox 匹配

## Review 意见

### 1. security_level 替代 allow_host_bash

从 bool 开关升级为 4 级安全模型：
- 0 = 完全信任（仅开发环境）
- 1 = 受限（默认，子进程隔离）
- 2 = 严格隔离（Docker 容器沙箱）
- 3 = 零信任（最小权限，生产环境）

### 2. 必须加 SandboxCapabilities

系统需要知道沙箱能做什么：bash、python、file_system、network、subprocess。这是 tool routing 的前置条件。

### 3. 不加 cpu/memory/disk/network policy

当前 LocalSandboxProvider 基于子进程，没有 cgroup / iptables / namespace 能力——加了字段也无法 enforcement。等切换到 Docker/E2B provider 时再加，同时补 enforcement 代码。

### 4. audit/logging 不放 config

属于运行时层（execution tracing / telemetry），不属于配置层。

---

## 采用的方案

```python
@dataclass
class SandboxCapabilities:
    bash: bool = True
    python: bool = False
    file_system: bool = True
    network: bool = False
    subprocess: bool = True

@dataclass
class SandboxConfig:
    use: str
    security_level: int = 1
    capabilities: SandboxCapabilities = field(default_factory=SandboxCapabilities)
    bash_output_max_chars: int = 20000
    bash_timeout_seconds: int = 600

    @property
    def allow_host_bash(self) -> bool:
        return self.security_level == 0
```

`allow_host_bash` 保留为 `@property`，从 `security_level` 派生，保持向后兼容。

## 架构决策

**配置层能力描述原则**：
- capabilities 是"声明沙箱能做什么"（declarative）——放 config 层
- cpu/memory/network 是"限制沙箱能用多少"（enforcement）——等 provider 支持才放 config 层
- audit/logging 是"记录沙箱做了什么"（observational）——属于 runtime 层

---

## 修改文件

- `backend/packages/lensmind/config/app_config.py` — SandboxCapabilities 新增 + SandboxConfig 增强
- `config.yaml` — security_level + capabilities
- `tests/test_config.py` — +4 测试用例

## 测试结果

15/15 passed
