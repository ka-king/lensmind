"""死循环检测中间件——检测 Agent 是否陷入重复的工具调用模式。

通过分析最近 N 轮的工具调用序列，识别循环模式并发出警告或中断。
"""

from langchain.agents.middleware import AgentMiddleware

__author__ = "万"


class LoopDetectionMiddleware(AgentMiddleware):
    """Agent 死循环检测器。

    完整实现将:
    - 追踪最近 K 轮的工具调用名称序列
    - 发现相同工具+相同参数的模式时标记为潜在循环
    - 轻则追加警告消息，重则清空 tool_calls 强制中断
    """

    pass
