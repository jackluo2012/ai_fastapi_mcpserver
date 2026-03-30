"""
安全模块
实现API Key鉴权和Origin校验
"""
import secrets
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.exceptions import AuthorizationError
import structlog

logger = structlog.get_logger()
settings = get_settings()

# HTTP Bearer Token安全方案
security = HTTPBearer(auto_error=False)


async def verify_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """
    验证API Key（FastAPI 依赖注入版本）
    支持两种方式：
    1. X-API-Key 头部
    2. Authorization: Bearer <key> 头部

    使用恒定时间比较防御时序攻击

    Note:
        当前 MCP 端点通过 ASGI 层面的 verify_api_key_asgi 进行鉴权。
        此函数保留用于未来非 MCP 的 FastAPI 路由鉴权（通过 Depends(verify_api_key) 使用）。

    Args:
        request: FastAPI请求对象
        x_api_key: X-API-Key头部值
        authorization: Authorization头部值（Bearer Token格式）

    Returns:
        str: 验证通过的API Key

    Raises:
        HTTPException: 当API Key无效时抛出403错误
    """
    api_key = None

    # 优先使用X-API-Key头部
    if x_api_key:
        api_key = x_api_key
    # 回退到Authorization Bearer Token
    elif authorization:
        api_key = authorization.credentials

    # 验证API Key
    if not api_key:
        logger.warning("api_key_missing", path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="缺少API Key，请提供X-API-Key头部或Authorization Bearer Token",
        )

    # 使用恒定时间比较防御时序攻击
    if not secrets.compare_digest(api_key, settings.MCP_API_KEY):
        logger.warning("api_key_invalid", path=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key无效",
        )

    logger.debug("api_key_verified", path=request.url.path)
    return api_key


def verify_origin(request: Request) -> None:
    """
    验证请求Origin
    防止DNS重绑定攻击

    Args:
        request: FastAPI请求对象

    Raises:
        AuthorizationError: 当Origin不在允许列表中时抛出异常
    """
    origin = request.headers.get("Origin")

    # 如果没有Origin头部（如直接API调用），跳过验证
    if not origin:
        return

    # 检查Origin是否在允许列表中
    if origin not in settings.ALLOWED_ORIGINS:
        logger.warning(
            "origin_not_allowed",
            origin=origin,
            allowed_origins=settings.ALLOWED_ORIGINS,
            path=request.url.path,
        )
        raise AuthorizationError(f"Origin '{origin}' 不在允许列表中")


async def verify_api_key_asgi(scope: dict, headers: dict) -> bool:
    """
    ASGI层面的API Key验证
    用于在ASGI中间件中验证API Key

    Args:
        scope: ASGI scope字典
        headers: ASGI headers字典（key为bytes）

    Returns:
        bool: 验证是否通过
    """
    api_key = None

    # 提取X-API-Key头部（ASGI中header key是bytes）
    x_api_key_header = headers.get(b"x-api-key")
    if x_api_key_header:
        api_key = x_api_key_header.decode("utf-8")
    else:
        # 尝试提取Authorization Bearer Token
        auth_header = headers.get(b"authorization")
        if auth_header:
            auth_value = auth_header.decode("utf-8")
            if auth_value.startswith("Bearer "):
                api_key = auth_value.split(" ", 1)[1]

    if not api_key:
        return False

    # 使用恒定时间比较
    return secrets.compare_digest(api_key, settings.MCP_API_KEY)
