"""
Prometheus指标定义模块
定义MCP工具执行相关的监控指标
"""
import inspect
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from prometheus_client import Counter, Histogram

# 定义工具执行耗时直方图
# Bucket针对工具执行时长优化，包含常见的长尾延迟
TOOL_DURATION = Histogram(
    "mcp_tool_execution_seconds",
    "MCP工具执行耗时（秒）",
    ["tool_name"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

# 定义工具执行总数计数器
TOOL_EXECUTION_TOTAL = Counter(
    "mcp_tool_execution_total",
    "MCP工具执行总数",
    ["tool_name", "status"],  # status: success, error
)

# 定义工具错误计数器
TOOL_ERRORS = Counter(
    "mcp_tool_errors_total",
    "MCP工具错误总数",
    ["tool_name", "error_type"],
)

# 类型变量，用于保持函数签名
F = TypeVar("F", bound=Callable[..., Any])


def track_tool_execution(tool_name: str) -> Callable[[F], F]:
    """
    工具执行监控装饰器
    自动记录工具的执行时间、成功/失败次数和错误类型

    Usage:
        @track_tool_execution(tool_name="hello_world")
        async def hello_world(name: str) -> str:
            return f"Hello, {name}!"

    Args:
        tool_name: 工具名称，用于指标标签

    Returns:
        装饰器函数
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            """异步函数包装器"""
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                # 记录成功
                TOOL_EXECUTION_TOTAL.labels(tool_name=tool_name, status="success").inc()
                return result
            except Exception as e:
                # 记录错误
                error_type = type(e).__name__
                TOOL_EXECUTION_TOTAL.labels(tool_name=tool_name, status="error").inc()
                TOOL_ERRORS.labels(tool_name=tool_name, error_type=error_type).inc()
                raise
            finally:
                # 记录执行时间
                duration = time.time() - start_time
                TOOL_DURATION.labels(tool_name=tool_name).observe(duration)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            """同步函数包装器"""
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                # 记录成功
                TOOL_EXECUTION_TOTAL.labels(tool_name=tool_name, status="success").inc()
                return result
            except Exception as e:
                # 记录错误
                error_type = type(e).__name__
                TOOL_EXECUTION_TOTAL.labels(tool_name=tool_name, status="error").inc()
                TOOL_ERRORS.labels(tool_name=tool_name, error_type=error_type).inc()
                raise
            finally:
                # 记录执行时间
                duration = time.time() - start_time
                TOOL_DURATION.labels(tool_name=tool_name).observe(duration)

        # 根据函数是否为协程选择对应的包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator
