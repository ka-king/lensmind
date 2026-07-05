"""工具错误处理中间件——将工具异常转为用户友好的消息。

拦截 wrap_tool_call 钩子，捕获工具调用中的异常，
转换为 ToolMessage(status="error") 让 Agent 感知并处理。
"""

from langchain.agents.middleware import AgentMiddleware

__author__ = "万"


class ToolErrorHandlingMiddleware(AgentMiddleware):
    """工具调用异常处理器。

    完整实现将:
    - 捕获超时异常，告知 Agent 重试或跳过
    - 捕获工具参数错误，提示正确的参数格式
    - 捕获外部服务错误，返回降级方案
    """

    pass
