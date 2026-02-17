"""
MCP 提示词模块
提供可复用的提示词模板，MCP 客户端可获取并使用
"""
from app.core.logging import get_logger
from app.mcp_server.app import mcp

logger = get_logger()


@mcp.prompt(name="code_review", description="代码审查提示词模板")
async def code_review_prompt(code: str, language: str = "python") -> str:
    """
    生成代码审查提示词。

    Args:
        code: 待审查的代码片段
        language: 编程语言，默认为 python
    """
    logger.info("prompt_accessed", prompt="code_review", language=language)
    return (
        f"请对以下 {language} 代码进行审查，关注以下方面：\n"
        f"1. 代码质量和可读性\n"
        f"2. 潜在的 Bug 或安全问题\n"
        f"3. 性能优化建议\n"
        f"4. 最佳实践遵循情况\n\n"
        f"代码：\n```{language}\n{code}\n```\n\n"
        f"请提供具体的改进建议。"
    )


@mcp.prompt(name="data_analysis", description="数据分析提示词模板")
async def data_analysis_prompt(data_description: str, goal: str = "综合分析") -> str:
    """
    生成数据分析提示词。

    Args:
        data_description: 数据描述
        goal: 分析目标
    """
    logger.info("prompt_accessed", prompt="data_analysis", goal=goal)
    return (
        f"请对以下数据进行 {goal}：\n\n"
        f"数据描述：{data_description}\n\n"
        f"请从以下角度进行分析：\n"
        f"1. 数据概览和基本统计\n"
        f"2. 关键趋势和模式\n"
        f"3. 异常值识别\n"
        f"4. 可行的建议和结论"
    )
