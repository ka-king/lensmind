# Review #001 — ModelConfig 增强

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 已修改

---

## Before/After

| | Before | After |
|---|--------|-------|
| 字段数 | 8 | 35 |
| 方法数 | 0 | 3 |
| 层数 | 1（扁平） | 8 层（核心→兜底） |
| extra 职责 | 滥捕（什么都在里面） | 兜底（仅未知字段） |
| 路由可用 | ❌ 无法判断模型能力 | ✅ supports_tools() |
| 成本可算 | ❌ | ✅ cost_estimate() |
| 密钥安全 | 直接写明文 | 支持 api_key_env |
| 生产韧性 | ❌ 无降级/限流 | fallback_models / rpm / tpm |

## 影响范围

| 文件 | 影响 | 说明 |
|------|------|------|
| `config.yaml` | ⚠️ 需补齐 | 模型配置按新字段补全 |
| `models/factory.py` | 🔄 已调整 | 新增 `_build_model_kwargs()` 消费新字段 |
| `agents/lead_agent/agent.py` | ✅ 无影响 | make_lead_agent() 通过 factory 间接调用 |
| `agents/factory.py` | ✅ 无影响 | 通过 factory 间接调用 |
| `subagents/builtins/*` | ✅ 无影响 | 子 Agent 配置在 subagents 段，独立 |
| `tools/task_tool.py` | ✅ 无影响 | 委托工具，不接触模型配置 |
| `sandbox/` | ✅ 无影响 | 沙箱配置独立 |

---

## 问题

当前 `ModelConfig` 字段太少，只有 8 个字段，`extra` 承担了太多不应该它承担的责任。

`extra` 是补丁区，不是核心设计区。但现有的温度、最大 token 之外的几乎所有参数都往 `extra` 里扔，导致：
- 类型不安全
- 系统逻辑无法基于字段做判断（如路由选模）
- UI 层无法结构化展示

---

## Review 意见

### 1. 补齐输出控制参数

很多模型都支持但没抽象出来：

- `top_p`
- `frequency_penalty`
- `presence_penalty`
- `stop`（停止词）
- `seed`（可复现）
- `response_format`（json / text / structured）

### 2. 增加 provider 层

当前 `use = module.path:ClassName` 是扁平结构，缺少：
- **provider** — openai / anthropic / azure / ollama / custom
- **base_url** — 自定义 API 端点（代理/网关）
- 不同 provider 的 base_url、header、鉴权方式差异

### 3. 补齐工程稳定性字段

生产环境必须有的：
- `timeout` — 请求超时
- `max_retries` — 最大重试次数
- `rpm` / `tpm` — 限流控制
- `fallback_models` — 模型降级列表（GPT-4o → Claude → Gemini）

### 4. 增加能力描述字段

用于 agent router / model selector：
- `context_window` — 上下文窗口大小
- `vision` — 是否支持图片输入
- `tools` — 是否支持工具调用
- `function_calling` — 是否支持 function calling
- `json_mode` — 是否支持 JSON 结构化输出

### 5. 安全 & 密钥管理

当前直接写 `api_key` 不够安全，增加：
- `api_key_env` — 指定环境变量名，读取时优先用环境变量
- 不直接存密钥明文

### 6. 成本与监控

商业系统必须：
- `input_cost_per_1k` — 每千输入 token 成本
- `output_cost_per_1k` — 每千输出 token 成本
- 用于 Agent 成本统计和自动选便宜模型

### 7. extra 的正确定位

核心原则：**满足以下任一条件就不应放 extra，必须升级为强类型字段**

- 被系统逻辑使用（router、fallback、cost、tool caller）
- 被 UI / 配置面板使用（可编辑、可展示）
- 需要类型校验（bool / int / enum / list）
- 被频繁访问

---

## 采用的方案

`ModelConfig` 按八层结构重新组织：

| 层 | 字段 |
|------|------|
| 核心标识 | `name`, `use`, `model`, `display_name` |
| provider + 鉴权 | `provider`, `base_url`, `api_key`, `api_key_env` |
| 生成控制 | `max_tokens`, `temperature`, `top_p`, `frequency_penalty`, `presence_penalty`, `stop`, `seed`, `response_format` |
| 能力描述 | `context_window`, `vision`, `tools`, `function_calling`, `json_mode` |
| 工程控制 | `timeout`, `max_retries`, `streaming` |
| 成本元数据 | `input_cost_per_1k`, `output_cost_per_1k` |
| 韧性策略 | `rpm`, `tpm`, `fallback_models` |
| 兜底 | `extra`（不在白名单的字段自动归入） |

新增方法：
- `resolve_api_key()` — 优先级：直接值 > 环境变量
- `supports_tools()` — 供路由逻辑判断
- `cost_estimate(input_tokens, output_tokens)` — 成本估算

`factory.py` 新增 `_build_model_kwargs()` 集中处理参数组装。

非白名单字段自动归入 `extra`，保留扩展性。

---

## 修改文件

- `backend/packages/lensmind/config/app_config.py` — ModelConfig 重写
- `backend/packages/lensmind/models/factory.py` — 新增 _build_model_kwargs()
- `config.yaml` — 示例配置更新
- `tests/test_config.py` — 新增 5 个测试用例

## 测试结果

8/8 passed
