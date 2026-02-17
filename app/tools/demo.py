"""
演示工具模块
包含Hello World等基础演示工具
"""
from app.core.logging import get_logger
from app.mcp_server.app import mcp_tool

logger = get_logger()


@mcp_tool(
    name="hello_world",
    description="基础连通性测试工具，返回问候语",
)
async def hello_world(name: str = "World") -> str:
    """
    Hello World工具
    用于测试MCP连接状态和基本功能

    Args:
        name: 要问候的名称，默认为"World"

    Returns:
        str: 问候语字符串

    Example:
        >>> await hello_world("Alice")
        "Hello, Alice! Enterprise MCP Server is running."
    """
    logger.info("executing_hello_world", user_name=name)
    result = f"Hello, {name}! Enterprise MCP Server is running."
    logger.debug("hello_world_completed", result=result)
    return result


@mcp_tool(
    name="echo",
    description="回显工具，返回输入的文本",
)
async def echo(text: str) -> str:
    """
    回显工具
    简单返回输入的文本，用于测试参数传递

    Args:
        text: 要回显的文本

    Returns:
        str: 回显的文本

    Example:
        >>> await echo("test")
        "test"
    """
    logger.info("executing_echo", text=text)
    return text
