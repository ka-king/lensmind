"""澄清反问工具——当用户需求模糊时主动提问。

ClarificationMiddleware 会拦截此工具的调用，
将问题格式化后返回给用户并暂停执行。
"""

from langchain_core.tools import tool

__author__ = "万"


@tool
def ask_clarification(question: str) -> str:
    """当用户需求不够明确时，向用户提一个澄清问题。

    适用场景:
    - 产品名称太模糊，无法确定品类
    - 用户没有指定视频风格
    - 时长要求与实际内容不匹配
    - 产品图片不够展示核心卖点

    参数:
        question: 要询问用户的澄清问题。

    返回:
        用户的回复文本。
    """
    return question
