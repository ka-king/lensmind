# LensMind — 配置指南

## 1. 配置文件

LensMind 使用两层配置：

| 文件 | 用途 | 是否提交 |
|------|------|---------|
| `config.yaml` | 项目级配置（模型、沙箱、子 Agent） | 是（不含密钥） |
| `.env` | 环境变量（API Key 等密钥） | 否 |

## 2. config.yaml 完整结构

```yaml
# === 配置版本（schema 迁移用）===
config_version: 1

# === 模型列表 ===
models:
  - name: claude-sonnet-4-6
    display_name: Claude Sonnet 4.6
    use: langchain_anthropic:ChatAnthropic
    model: claude-sonnet-4-6
    api_key: $ANTHROPIC_API_KEY
    max_tokens: 4096
    temperature: 0.7

  - name: claude-opus-4-7
    display_name: Claude Opus 4.7（编剧）
    use: langchain_anthropic:ChatAnthropic
    model: claude-opus-4-7
    api_key: $ANTHROPIC_API_KEY
    max_tokens: 8192
    temperature: 0.8

  - name: gpt-4o
    display_name: GPT-4o
    use: langchain_openai:ChatOpenAI
    model: gpt-4o
    api_key: $OPENAI_API_KEY

  - name: flux-pro
    display_name: Flux Pro（图片生成）
    use: lensmind.models.image_gen_provider:FluxProvider
    api_key: $FLUX_API_KEY

  - name: runway-gen-3
    display_name: Runway Gen-3（视频生成）
    use: lensmind.models.video_gen_provider:RunwayProvider
    api_key: $RUNWAY_API_KEY

# === 默认模型 ===
default_model: claude-sonnet-4-6

# === 子 Agent 配置 ===
subagents:
  timeout_seconds: 1800    # 全局默认 30 分钟

  agents:
    # 产品分析师：轻量模型，快速分析
    product_analyzer:
      model: claude-sonnet-4-6
      timeout_seconds: 60
      max_turns: 10

    # 编剧：强模型，需要创意
    script_writer:
      model: claude-opus-4-7
      timeout_seconds: 120
      max_turns: 20

    # 模特图生成师：图片模型
    model_image_artist:
      model: flux-pro
      timeout_seconds: 300
      max_turns: 5

    # 场景设计师：图片模型
    scene_designer:
      model: flux-pro
      timeout_seconds: 300
      max_turns: 5

    # 分镜动画师：视频模型
    storyboard_animator:
      model: runway-gen-3
      timeout_seconds: 600
      max_turns: 6

    # 剪辑师：不需要 LLM，直接调工具
    video_editor:
      timeout_seconds: 300
      max_turns: 8

# === 沙箱 ===
sandbox:
  use: lensmind.sandbox.local:LocalSandboxProvider
  allow_host_bash: false
  bash_output_max_chars: 20000
  bash_timeout_seconds: 600

# === Skill 路径 ===
skills:
  public_path: skills/public/
  system_path: .agent/skills/

# === 记忆 ===
memory:
  enabled: true
  max_facts: 50
  max_injection_tokens: 2000

# === 摘要（长对话自动压缩）===
summarization:
  enabled: true
  trigger:
    - type: tokens
      value: 4000
  keep:
    type: messages
    value: 20

# === 标题自动生成 ===
title:
  enabled: true

# === 中间件 ===
features:
  sandbox: true
  memory: true
  summarization: true
  subagent: true
  vision: true
  auto_title: true
  loop_detection: true
  guardrail: true
```

## 3. .env 示例

```bash
# LLM
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# 图片生成
FLUX_API_KEY=...

# 视频生成
RUNWAY_API_KEY=...
KELING_AK=...
KELING_SK=...

# TTS
OPENAI_TTS_API_KEY=...
AZURE_SPEECH_KEY=...
AZURE_SPEECH_REGION=eastasia

# 存储
OUTPUT_DIR=./output
```

## 4. 配置优先级

```
代码参数 > 环境变量 > config.yaml > 默认值
```

`config.yaml` 中 `$VAR_NAME` 语法自动从环境变量读取，不写密钥到配置文件。

## 5. 配置版本迁移

```bash
# 当 config.example.yaml 版本号更新时
make config-upgrade

# 自动合并新字段到你的 config.yaml，保留已有值
# 备份: config.yaml.bak
```
