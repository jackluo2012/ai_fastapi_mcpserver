"""
工具基类和通用装饰器
提供工具开发的基类和通用功能
"""
from typing import Any, Callable, TypeVar

from app.core.logging import get_logger
from app.utils.metrics import track_tool_execution

logger = get_logger()

# 类型变量
F = TypeVar("F", bound=Callable[..., Any])


def create_mcp_tool_decorator(mcp_instance: Any):
    """
    创建MCP工具装饰器工厂函数
    避免循环导入问题

    Args:
        mcp_instance: MCP服务器实例

    Returns:
        mcp_tool装饰器函数
    """

    def mcp_tool(
        name: str, description: str, **tool_kwargs: dict[str, Any]
    ) -> Callable[[F], F]:
        """
        MCP工具装饰器
        结合监控装饰器，为工具添加自动监控能力

        Args:
            name: 工具名称
            description: 工具描述
            **tool_kwargs: 传递给MCP工具装饰器的其他参数

        Returns:
            装饰器函数

        Example:
            @mcp_tool(name="hello", description="问候工具")
            async def hello(name: str) -> str:
                return f"Hello, {name}!"
        """

        def decorator(func: F) -> F:
            # 先应用监控装饰器
            monitored_func = track_tool_execution(tool_name=name)(func)
            # 再应用MCP工具装饰器
            return mcp_instance.tool(name=name, description=description, **tool_kwargs)(monitored_func)  # type: ignore

        return decorator

    return mcp_tool
