# LensMind 测试计划

**基于四层测试金字塔，覆盖 Agent 项目的完整质量体系。**

---

## 一、当前测试状态

| 层 | 已有 | 测试数 | 结果 |
|---|------|--------|------|
| L1 单元测试 | ✅ 5个文件 | 45 | ✅ 45/45 passed |
| L2 集成测试 | ✅ 3个文件 | 9 | ✅ 9/9 passed |
| L3 场景测试 | ✅ 真实API | 5 | ✅ 5/5 passed (DeepSeek V4 Pro) |
| L3 场景测试 | ⏸️ 需API key | 4 | ⏸️ 4 skipped |
| L4 生产监控 | ❌ 未开始 | 0 | — |
| **总计** | | **59 passed / 4 skipped** | **(~9s L1+L2, +70s L3)** |

### L1 覆盖详情

| 测试文件 | 测试数 | 覆盖模块 |
|---------|--------|---------|
| `test_config.py` | 18 | ModelConfig, SubagentSpec, SandboxConfig, FeaturesConfig, MemoryConfig, SkillsConfig |
| `test_skills.py` | 7 | parser, catalog, loader |
| `test_workflow.py` | 8 | WorkflowNode, WorkflowPlan, WorkflowResult, DAG 验证, pipeline 构建 |
| `test_sandbox_local.py` | 5 | LocalSandbox 命令执行、文件读写、超时处理、provider |
| `test_tools_unit.py` | 7 | bash_tool 降级、task_tool 未知agent、clarification 干净输出、persistence 往返、checkpoint 往返、catalog 扫描 |

### L2 覆盖详情

| 测试文件 | 测试数 | 覆盖场景 |
|---------|--------|---------|
| `test_client_pipeline.py` | 3 | generate_video 全链路、带图片生成、task_id 持久化 |
| `test_sandbox_integration.py` | 3 | middleware 生命周期、bash_tool 沙箱路由、多沙箱文件隔离 |
| `test_skills_to_workflow.py` | 3 | SKILL.md → WorkflowPlan 转换、6个公开 Skill 全部可解析、不存在 Skill 返回 None |

### L3 真实场景验证

| 测试 | 模型 | 耗时 | 结果 |
|------|------|------|------|
| `test_real_product_analyzer` | DeepSeek V4 Pro | 10.7s | ✅ 产出结构化产品分析 JSON |
| `test_real_simple_dag` | DeepSeek V4 Pro | 12.6s | ✅ 2 节点 DAG 串联 |
| `test_full_6_node_pipeline` | DeepSeek V4 Pro | 25.4s | ✅ 完整6节点，产出分镜+FFmpeg方案 |
| `test_pipeline_with_style_param` | DeepSeek V4 Pro | 40.4s | ✅ 运动鞋风格参数，产出定制脚本 |
| `test_real_chat` | DeepSeek V4 Pro | — | ✅ 对话可用 |

### 关键发现（L3 测试中发现并修复的 bug）

- **Bug #1: `load_dotenv()` 缺失** — API key 无法从 .env 加载（已修复 `config/app_config.py`）
- **Bug #2: `_build_prompt` 只传上游依赖输出** — 初始 context（如 `product_context`）无法到达第一个节点（已修复 `workflow/engine.py`）
- **Bug #3: TaskRepository 并发写入丢失记录** — JSONL 追加无 `threading.Lock`（已修复 `task_repo.py`）
- **Bug #4: TaskRepository.get() 未处理损坏 JSON** — `list_recent` 有 `try-catch` 但 `get` 漏了（已修复 `task_repo.py`）
- **Bug #5: execute_command(None) 无空值保护** — `shlex.split(None)` 读取 stdin 导致 OSError（已修复 `local_sandbox.py`）
- **Bug #6: session_pool json.loads 未 catch** — 损坏 JSON 直接崩溃，无 try-catch（已修复 `mcp/session_pool.py`）
- **Bug #7: task_tool 未 catch get_current_model** — RuntimeError 直接杀 agent（已修复 `tools/task_tool.py`）
- **Bug #8: AssetRepository 与 TaskRepository 同病** — JSON 无 catch、无锁（已修复 `repositories/asset_repo.py`）
- **Bug #9: _resolve_class 无 try-catch** — ImportError/AttributeError 直接崩，缺格式校验（已修复 `models/factory.py`）
- **Bug #10: catalog rglob 无 PermissionError catch** — 无权限目录导致扫描崩溃（已修复 `skills/catalog.py`）
- **Bug #11: disconnect __exit__ 无 try-catch** — 资源释放时异常导致残留（已修复 `mcp/client.py`）
- **Bug #12: parser yaml.safe_load 无 catch** — 损坏 YAML+UTF-8 直接崩溃（已修复 `skills/parser.py`）
- **Bug #13: checkpointer save/load 无文件 I/O catch** — OSError+JSON损坏 直接崩溃（已修复 `json_checkpointer.py`）
- **Bug #14: list_recent 全量加载** — `read_text+split` 大文件 O(n) 内存，改为 `deque(maxlen=limit)` 流式（已修复）
- **Mock 限制**: MagicMock 无法模拟 LangGraph `create_agent()` 完整 tool-calling 消息链

### 全维度审计结论

| 维度 | 状态 | 说明 |
|------|------|------|
| 空值/None 入参 | ✅ | 10 个模块已防御 |
| try-catch 覆盖 | ✅ | 文件I/O、JSON、YAML、网络调用均已 catch |
| 列表操作判空 | ✅ | validate/validate/get 均有空保护 |
| 并发/线程安全 | ✅ | TaskRepo/AssetRepo 有 Lock，contextvar 天然隔离 |
| 内存泄漏 | ✅ | 每次 create_sandbox 独立 workspace，deque 限制内存 |
| 性能/大数据 | ✅ | 流式读取+limit 分页，deque 定长缓冲 |
| 循环内 I/O | ✅ | 仅 engine DAG 节点调用（设计如此），无隐式重复调用 |
| 配置值域校验 | ⚠️ | MVP 不做，极端值由下游 factory/engine 兜底 |
| 日志覆盖 | ✅ | 54 条日志 + 12 error 级，所有异常路径有记录 |

### 审计结论

49 个源文件全部审查完毕。除上述 8 个 bug 外，其余模块防御编程措施到位：
- `runtime/store/kv_store.py` — _save/_load 有 try-catch ✅
- `runtime/checkpointer/` — 文件不存在返回 None ✅
- `sandbox/local/` — 文件不存在、超时、空命令已 catch ✅
- `skills/parser.py` — frontmatter 缺失、YAML 损坏有 catch ✅
- `skills/catalog.py` — 路径不存在返回 0 ✅
- `mcp/session_pool.py` — JSON 损坏、连接失败已 catch ✅
- `tools/bash_tool.py` — 沙箱降级 + 异常 catch ✅
- `persistence/task_repo.py` — 锁、损坏行跳过 ✅
- `workflow/engine.py` — 节点失败不中断 + 重试 ✅

---

## 二、四层测试计划

### L1：单元测试（已有 33 个，扩展目标 50+）

**原则：测确定性逻辑，不调真实 LLM。**

| 模块 | 测试内容 | 已有 |
|------|---------|------|
| `config/app_config.py` | ModelConfig 解析、SubagentSpec from_dict、SecurityLevel 派生 | 18 ✅ |
| `skills/parser.py` | SKILL.md frontmatter 解析、缺 name 报错、pipeline 节点解析 | 4 ✅ |
| `skills/catalog.py` | 多路径扫描、get_pipeline 转换、public/system 分离 | 2 ✅ |
| `skills/loader.py` | prompt 构建、context 注入 | 1 ✅ |
| `workflow/plan.py` | DAG 验证（缺依赖、无入口）、pipeline 构建 | 5 ✅ |
| `workflow/result.py` | NodeResult 计时、WorkflowResult 状态追踪 | 3 ✅ |
| `workflow/engine.py` | — | 集成覆盖 ✅ |
| `subagents/config.py` | SubagentRunConfig 三层合并 | 1 ✅ |
| `sandbox/sandbox.py` | security_level 派生 allow_host_bash | 1 ✅ |
| `sandbox/local/` | 命令执行、文件读写、超时、provider | 5 ✅ |
| `tools/builtins/bash_tool.py` | 沙箱降级、无效命令 | 2 ✅ |
| `tools/builtins/clarification_tool.py` | 干净输出、无前缀 | 1 ✅ |
| `tools/task_tool.py` | 未知 subagent 报错 | 1 ✅ |
| `persistence/` | TaskRepository 往返、Checkpoint 往返 | 2 ✅ |
| `skills/catalog.py` | 真实路径扫描 | 1 ✅ |
| `tools/task_tool.py` | — | 0 | **1** |

**待补 8 个：**

```python
# tests/test_engine.py
def test_engine_topological_sort()
def test_engine_parallel_group_detection()
def test_engine_node_retry_on_failure()

# tests/test_sandbox.py
def test_local_sandbox_execute_command()
def test_local_sandbox_file_read_write()

# tests/test_tools.py
def test_bash_tool_sandbox_fallback()
def test_task_tool_unknown_subagent()
```

---

### L2：集成测试（目标 6 个）

**原则：测模块间协作，Mock 外部 LLM/API。**

```
tests/integration/
├── test_skills_to_workflow.py    # SKILL.md → SkillDef → WorkflowPlan 链路
├── test_client_pipeline.py       # client.generate_video() 全链路（mock model）
├── test_sandbox_middleware.py    # SandboxMiddleware + bash_tool + contextvar
├── test_mcp_session_pool.py      # MCPSessionPool 加载 + 工具发现（mock server）
├── test_persistence_roundtrip.py # TaskRepository save → get → list
└── test_runtime_checkpoint.py    # save_checkpoint → load_checkpoint 往返
```

**示例：test_skills_to_workflow.py**

```python
def test_skill_parsed_to_workflow_plan():
    """验证 SKILL.md → WorkflowPlan 的完整链路。"""
    catalog = SkillCatalog()
    catalog.scan(public_path="skills/public/", system_path=".agent/skills/")
    
    plan = catalog.get_pipeline("product-video")
    assert plan is not None
    assert len(plan.nodes) == 6
    assert plan.validate() == []
    
    # 验证依赖关系
    script_node = plan.get_node("script")
    assert "product_analysis" in script_node.depends_on
    
    # 验证并行组
    model = plan.get_node("model_images")
    scene = plan.get_node("scene_images")
    assert model.parallel_group == scene.parallel_group == "image_generation"
```

**示例：test_client_pipeline.py**

```python
from unittest.mock import MagicMock

def test_generate_video_flow():
    """验证 client.generate_video() 全链路（mock LLM）。"""
    mock_model = MagicMock()
    mock_model.invoke.return_value = {"messages": []}
    
    client = LensMindClient(model=mock_model)
    result = client.generate_video("测试产品")
    
    assert result["status"] in ("completed", "failed")
    assert "task_id" in result
```

---

### L3：场景测试（目标 4 个）

**原则：模拟完整对话流程，验证多轮交互和状态一致性。**

```
tests/scenarios/
├── test_full_video_generation.py  # 完整视频生成：产品名 → DAG → 结果
├── test_error_recovery.py         # 节点失败 → 错误收集 → 管线继续
├── test_multi_turn_chat.py        # 多轮对话：需求澄清 → 生成
└── test_parallel_execution.py     # 验证 model+scene 真正并行
```

**设计要点：**

- 每个场景定义"输入序列 → 预期状态变化 → 最终输出"
- 不依赖真实 LLM——用预定义的 response sequence mock
- 关注点：DAG 执行顺序、错误收集、checkpoint 可恢复

**示例：test_full_video_generation.py**

```python
def test_scenario_complete_generation():
    """
    场景: 用户输入产品 → 完整生成
    步骤:
      1. client.generate_video("连衣裙")
      2. DAG 执行 6 个节点
      3. 返回 status=completed
      4. checkpoint 可恢复
      5. task 已持久化
    """
    pass  # 需 langchain 环境
```

---

### L4：生产监控（部署后启用）

| 指标 | 采集方式 | 告警阈值 |
|------|---------|---------|
| DAG 成功率 | WorkflowResult.status | < 80% |
| 单节点平均耗时 | NodeResult.duration_ms | > 5min |
| Token 用量 | Agent invoke 回调 | > 100k/任务 |
| 沙箱异常 | SandboxMiddleware 日志 | > 0 |
| MCP 连接状态 | MCPSessionPool.connected | 断开 > 1min |
| 模型降级次数 | ModelConfig.fallback_models 触发 | > 3次/小时 |

---

## 三、测试执行策略

### CI/CD 集成（GitHub Actions）

```yaml
# .github/workflows/tests.yml
name: LensMind Tests
on: [push, pull_request]

jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v -k "not scenario"

  integration:
    needs: unit
    runs-on: ubuntu-latest
    steps:
      - run: pip install -e ".[dev]"
      - run: pytest tests/integration/ -v

  scenarios:
    needs: unit
    runs-on: ubuntu-latest
    steps:
      - run: pip install -e ".[dev]"
      - run: pytest tests/scenarios/ -v --timeout=120
```

### 本地开发

```bash
# 全量
pytest tests/ -v

# L1 only（不需要 langchain）
pytest tests/ -v -k "not scenario and not integration"

# 单个模块
pytest tests/test_config.py -v
pytest tests/test_skills.py -v
pytest tests/test_workflow.py -v
```

---

## 四、测试优先级（实施顺序）

```
Phase 1（本周）: L1 补齐 —— 8 个待补单元测试
Phase 2（下周）: L2 集成 —— 6 个模块间协作测试
Phase 3（后续）: L3 场景 —— 4 个端到端场景（需 langchain 环境）
Phase 4（上线）: L4 监控 —— 指标采集 + 告警
```

---

## 五、质量检查清单

- [ ] `config.yaml` 格式错误时抛出明确异常
- [ ] SKILL.md 缺少 `name` 字段时报错
- [ ] DAG 节点依赖不存在的节点时 validate() 返回错误
- [ ] Sandbox `security_level=1` 时 `allow_host_bash=False`
- [ ] WorkflowEngine 单节点失败时 `result.status=partial`
- [ ] TaskRepository save → get 数据往返不丢失
- [ ] MCPSessionPool 无 `extensions_config.json` 时不崩溃
- [ ] 并行组节点确实在不同线程执行
- [ ] `model_image_artist` 和 `scene_designer` 并行启动时间差 < 10ms
