"""
MCP 资源模块
提供服务器信息、运行状态等资源的 MCP Resource 注册
"""
import json
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.logging import get_logger
from app.mcp_server.app import mcp

logger = get_logger()
settings = get_settings()


@mcp.resource(
    "resource://server-info",
    name="server_info",
    description="服务器基本信息和配置",
)
async def server_info_resource() -> str:
    """
    返回服务器基本信息，包括项目名称、版本等。
    MCP 客户端可通过此资源了解服务器配置。
    """
    info = {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mcp_endpoint": "/mcp",
        "prometheus_enabled": settings.PROMETHEUS_ENABLED,
    }
    logger.info("resource_accessed", resource="server_info")
    return json.dumps(info, ensure_ascii=False, indent=2)


@mcp.resource(
    "resource://server-status",
    name="server_status",
    description="服务器运行状态",
)
async def server_status_resource() -> str:
    """
    返回服务器当前运行状态信息。
    """
    status = {
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "log_level": settings.LOG_LEVEL,
    }
    logger.info("resource_accessed", resource="server_status")
    return json.dumps(status, ensure_ascii=False, indent=2)
