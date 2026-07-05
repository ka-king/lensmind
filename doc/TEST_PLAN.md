# LensMind 测试计划

**基于四层测试金字塔，覆盖 Agent 项目的完整质量体系。**

---

## 一、当前测试状态

| 层 | 已有 | 测试数 |
|---|------|--------|
| L1 单元测试 | ✅ `test_config.py` `test_skills.py` `test_workflow.py` | 33 |
| L2 集成测试 | ❌ 未开始 | 0 |
| L3 场景测试 | ❌ 未开始 | 0 |
| L4 生产监控 | ❌ 未开始 | 0 |

---

## 二、四层测试计划

### L1：单元测试（已有 33 个，扩展目标 50+）

**原则：测确定性逻辑，不调真实 LLM。**

| 模块 | 测试内容 | 已有 | 待补 |
|------|---------|------|------|
| `config/app_config.py` | ModelConfig 解析、SubagentSpec from_dict、SecurityLevel 派生 | 15 | — |
| `skills/parser.py` | SKILL.md frontmatter 解析、缺 name 报错、pipeline 节点解析 | 4 | — |
| `skills/catalog.py` | 多路径扫描、get_pipeline 转换、public/system 分离 | 2 | — |
| `skills/loader.py` | prompt 构建、context 注入 | 1 | — |
| `workflow/plan.py` | DAG 验证（缺依赖、无入口）、pipeline 构建 | 5 | 1 |
| `workflow/result.py` | NodeResult 计时、WorkflowResult 状态追踪 | 3 | — |
| `workflow/engine.py` | — | 0 | **3** |
| `subagents/config.py` | SubagentRunConfig 三层合并 | 1 | — |
| `sandbox/sandbox.py` | security_level 派生 allow_host_bash | 1 | — |
| `sandbox/local/` | — | 0 | **2** |
| `tools/builtins/bash_tool.py` | — | 0 | **1** |
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
