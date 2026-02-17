"""
全局异常处理模块
定义自定义异常类和全局异常处理器
"""
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()


class MCPException(Exception):
    """MCP相关异常基类"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(MCPException):
    """认证错误异常"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class AuthorizationError(MCPException):
    """授权错误异常"""

    def __init__(self, message: str = "授权失败"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class ValidationError(MCPException):
    """验证错误异常"""

    def __init__(self, message: str = "请求参数验证失败"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


async def mcp_exception_handler(request: Request, exc: MCPException) -> JSONResponse:
    """
    MCP异常处理器
    捕获MCP相关异常并返回标准JSON响应

    Args:
        request: FastAPI请求对象
        exc: MCP异常实例

    Returns:
        JSONResponse: 标准化的错误响应
    """
    logger.error(
        "mcp_exception",
        exception_type=type(exc).__name__,
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "type": type(exc).__name__},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    请求验证异常处理器
    处理Pydantic验证错误

    Args:
        request: FastAPI请求对象
        exc: 验证异常实例

    Returns:
        JSONResponse: 标准化的验证错误响应
    """
    errors = exc.errors()
    logger.warning(
        "validation_error",
        errors=errors,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors, "type": "ValidationError"},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器
    捕获所有未处理的异常，记录完整堆栈跟踪

    Args:
        request: FastAPI请求对象
        exc: 异常实例

    Returns:
        JSONResponse: 标准化的错误响应（脱敏后）
    """
    logger.exception(
        "unhandled_exception",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "内部服务器错误",
            "type": "InternalServerError",
        },
    )
