"""
系统级工具模块
包含系统信息、健康检查等系统相关工具
"""
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.logging import get_logger
from app.mcp_server.app import mcp_tool

logger = get_logger()
settings = get_settings()


@mcp_tool(
    name="get_server_info",
    description="获取服务器信息，包括版本、配置等",
)
async def get_server_info() -> dict:
    """
    获取服务器信息工具
    返回服务器的基本信息和配置

    Returns:
        dict: 包含服务器信息的字典

    Example:
        >>> await get_server_info()
        {
            "project_name": "Enterprise MCP Server",
            "version": "1.0.0",
            "timestamp": "2025-02-13T10:00:00"
        }
    """
    logger.info("executing_get_server_info")
    info = {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    logger.debug("server_info_retrieved", info=info)
    return info


@mcp_tool(
    name="fetch_external_data",
    description="使用异步HTTP客户端获取外部API数据",
)
async def fetch_external_data(url: str) -> dict:
    """
    获取外部数据工具
    演示使用异步HTTP客户端调用外部API

    Args:
        url: 要获取数据的URL

    Returns:
        dict: 外部API返回的JSON数据

    Raises:
        httpx.HTTPStatusError: 当HTTP请求失败时
        httpx.RequestError: 当网络请求错误时

    Example:
        >>> await fetch_external_data("https://api.example.com/data")
        {"data": "..."}
    """
    from app.utils.http_client import http_client

    logger.info("fetching_external_data", url=url)
    try:
        data = await http_client.get(url)
        logger.info("external_data_fetched", url=url, data_size=len(str(data)))
        return data
    except Exception as e:
        logger.error("external_data_fetch_failed", url=url, error=str(e))
        raise
