"""子 Agent 限制中间件——防止无限创建子 Agent 导致资源耗尽。

在 after_model 阶段检查 task_tool 调用次数，超出限制时截断。
"""

from langchain.agents.middleware import AgentMiddleware

__author__ = "万"


class SubagentLimitMiddleware(AgentMiddleware):
    """子 Agent 并发数量限制器。

    完整实现将:
    - 限制单次对话的子 Agent 调用总数
    - 限制同一类型子 Agent 的重复调用
    - 超出限制时返回友好提示而非直接报错
    """

    pass
