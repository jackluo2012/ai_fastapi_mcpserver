"""
Streamable HTTP传输层模块
封装MCP SDK的Streamable HTTP应用，添加鉴权中间件
"""
from typing import Callable

from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import verify_api_key_asgi
from app.mcp_server.app import mcp

logger = get_logger()
settings = get_settings()


def _scope_summary(scope: dict) -> dict:
    """从 ASGI scope 提取用于日志的摘要（不包含 body）。"""
    path = scope.get("path", "")
    method = scope.get("method", "")
    root_path = scope.get("root_path", "")
    query_string = scope.get("query_string", b"")
    return {
        "path": path,
        "method": method,
        "root_path": root_path,
        "query_string": query_string.decode("utf-8", errors="replace") if query_string else "",
        "scope_type": scope.get("type"),
    }


def create_protected_mcp_app() -> Callable:
    """
    创建受保护的MCP应用
    在ASGI层面添加API Key鉴权

    Returns:
        Callable: ASGI应用函数
    """

    # 获取MCP SDK生成的Streamable HTTP ASGI应用
    mcp_asgi_app = mcp.streamable_http_app()

    async def protected_mcp_app(scope: dict, receive: Callable, send: Callable) -> None:
        """
        受保护的MCP ASGI应用
        在请求进入MCP SDK处理前进行API Key验证

        Args:
            scope: ASGI scope字典
            receive: ASGI receive函数
            send: ASGI send函数
        """
        scope_type = scope.get("type", "")
        summary = _scope_summary(scope) if scope_type == "http" else {"scope_type": scope_type}

        # 仅处理HTTP请求
        if scope_type != "http":
            logger.info("mcp_request_non_http", **summary)
            await mcp_asgi_app(scope, receive, send)
            return

        # 请求进入日志（便于排查 502：确认请求是否到达、path 是否正确）
        headers = dict(scope.get("headers", []))
        has_auth = bool(headers.get(b"authorization") or headers.get(b"x-api-key"))
        logger.info(
            "mcp_request_in",
            **summary,
            has_auth_header=has_auth,
        )

        # 验证API Key（必须 await，verify_api_key_asgi 为 async）
        if not await verify_api_key_asgi(scope, headers):
            response = JSONResponse(
                status_code=403,
                content={"detail": "未授权访问MCP端点，请提供有效的API Key"},
            )
            await response(scope, receive, send)
            logger.warning(
                "mcp_endpoint_unauthorized",
                **summary,
            )
            return

        logger.info("mcp_request_authorized", **summary)

        try:
            logger.info("mcp_delegate_start", **summary)
            await mcp_asgi_app(scope, receive, send)
            logger.info("mcp_delegate_done", **summary)
        except Exception as e:
            exc_type = type(e).__name__
            logger.exception(
                "mcp_request_failed",
                error=str(e),
                exc_type=exc_type,
                **summary,
            )
            try:
                response = JSONResponse(
                    status_code=500,
                    content={"detail": "MCP 请求处理异常", "type": "InternalServerError"},
                )
                await response(scope, receive, send)
                logger.info("mcp_response_500_sent", **summary, exc_type=exc_type)
            except Exception as send_err:
                logger.exception(
                    "mcp_response_500_send_failed",
                    send_error=str(send_err),
                    **summary,
                )
                raise

    return protected_mcp_app
