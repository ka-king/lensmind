# 沙箱设计

## 1. 为什么要沙箱

LensMind 的核心操作涉及大量不安全的执行：

| 操作 | 风险 |
|------|------|
| FFmpeg 视频合成 | 命令注入、资源耗尽 |
| 用户上传产品图 | 恶意文件、路径穿越 |
| AI 图片下载/写入 | 磁盘占满、文件覆盖 |
| Python 脚本执行 | 任意代码执行 |

所有以上操作全部在沙箱内隔离执行。

## 2. 架构

```
Agent Tool Call
    │
    ▼
┌─────────────────────┐
│ SandboxMiddleware    │  ← 拦截 Bash/文件 tool call
│ (AgentMiddleware)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ SandboxProvider      │  ← 工厂：创建沙箱实例
│ (可插拔)            │
└──────────┬──────────┘
           │
    ┌──────┴──────────┐
    │                  │
    ▼                  ▼
┌──────────┐    ┌──────────┐
│ Local    │    │ Docker   │
│ Sandbox  │    │ Sandbox  │  (生产环境)
│ (MVP)   │    │          │
└──────────┘    └──────────┘
```

## 3. 抽象基类

```python
class Sandbox(ABC):
    """沙箱抽象基类"""

    @abstractmethod
    def execute_command(
        self,
        command: str,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        """执行 Bash 命令"""

    @abstractmethod
    def read_file(self, path: str) -> str:
        """读取文件"""

    @abstractmethod
    def write_file(self, path: str, content: str) -> None:
        """写入文件"""

    @abstractmethod
    def list_dir(self, path: str) -> list[str]:
        """列出目录"""

    @abstractmethod
    def glob(self, pattern: str) -> list[str]:
        """文件匹配"""
```

## 4. 本地沙箱实现（MVP）

```python
class LocalSandboxProvider(SandboxProvider):
    """子进程隔离的本地沙箱"""

    def create_sandbox(self) -> Sandbox:
        workspace = tempfile.mkdtemp(prefix="lensmind_sandbox_")
        return LocalSandbox(
            id=str(uuid.uuid4()),
            workspace=workspace,
            allow_host_bash=False,  # 禁止直接宿主机 Bash
            bash_timeout_sec=600,   # 10 分钟超时
        )
```

## 5. 安全配置（config.yaml）

```yaml
sandbox:
  use: lensmind.sandbox.local:LocalSandboxProvider

  # MVP 阶段禁止宿主机 Bash
  allow_host_bash: false

  # 限制
  bash_output_max_chars: 20000     # Bash 输出截断
  read_file_output_max_chars: 50000 # 文件读取截断
  bash_timeout_seconds: 600        # 单命令最大执行时间

  # 允许的工具白名单
  allowed_tools:
    - ffmpeg
    - python3
    - convert     # ImageMagick
    - identify
```

## 6. 沙箱生命周期

```
Agent 启动
    │
    ▼
before_agent → SandboxMiddleware.before_agent() → 创建沙箱
    │
    ▼
工具调用 → SandboxMiddleware 拦截 → 路由到沙箱
    │         · Bash → sandbox.execute_command()
    │         · 文件 → sandbox.read_file() / write_file()
    ▼
after_agent → SandboxMiddleware.after_agent() → 清理沙箱
```

## 7. LensMind 特有场景

### FFmpeg 合成

```python
# 不是直接在宿主机跑 FFmpeg
# 而是通过 sandbox.execute_command()
result = sandbox.execute_command(
    command="ffmpeg -i /sandbox/clip_01.mp4 -i /sandbox/tts.mp3 ... /sandbox/final.mp4",
    timeout=300,
    env={"TMPDIR": "/sandbox/tmp"}
)
```

### 图片处理

```python
# 用户上传的产品图 → 先入沙箱 → 再分析
sandbox.write_file("/sandbox/uploads/dress.jpg", uploaded_bytes)
sandbox.execute_command("identify /sandbox/uploads/dress.jpg")
```
