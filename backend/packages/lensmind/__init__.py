"""LensMind — AI 电商视频生成智能体。

多 Agent 协作架构：
- Lead Agent（电商视频主编）编排 6 个专业子 Agent
- Skill 市场（skills/public/）插件式装卸能力
- 中间件链（沙箱隔离、错误处理、子Agent限制、死循环检测）
- MCP 协议接入外部 AI 服务（图片/视频/TTS）
- YAML 驱动配置（一条 config.yaml 控制所有行为）
"""

__version__ = "0.1.0"
__author__ = "万"
