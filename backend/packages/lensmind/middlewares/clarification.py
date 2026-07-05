"""需求澄清中间件——拦截 ask_clarification 工具调用。

必须在中间件链的最后一个位置。
这样 after_model 反序执行时最先拦截 ask_clarification，
通过 Command(goto=END) 暂停执行，等用户回复后继续。
"""

from langchain.agents.middleware import AgentMiddleware

__author__ = "万"


class ClarificationMiddleware(AgentMiddleware):
    """澄清反问拦截器——位置必须在最后。

    为什么必须在最后:
    中间件链反序执行 after_model 钩子。
    放在最后 → 第一个拦截 AI 输出 → 发现 ask_clarification →
    立即暂停执行，避免其他中间件处理已被拦截的消息。
    """

    pass
