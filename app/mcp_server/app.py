"""
MCP服务器应用模块
初始化MCP服务器实例并注册工具、资源和提示词
"""
from mcp.server.fastmcp import FastMCP

from app.core.logging import get_logger
from app.tools.base import create_mcp_tool_decorator

logger = get_logger()

# 初始化MCP服务器实例
# streamable_http_path="/" 使挂载到 /mcp 时子应用收到 path="/" 能命中路由，避免 404
# stateless_http=True 表示无需先 initialize，每次请求独立处理，适合直接调用 tools/list 等
mcp = FastMCP(
    "Enterprise-Demo-MCP",
    streamable_http_path="/",
    stateless_http=True,
)

# 创建工具装饰器并导出，供tools模块使用
mcp_tool = create_mcp_tool_decorator(mcp)

# 导入工具模块以触发装饰器注册
# 注意：必须在mcp实例创建后导入，这样装饰器才能正确注册工具
from app.tools import demo, system, resources, prompts  # noqa: E402

logger.info("mcp_server_initialized", server_name="Enterprise-Demo-MCP")

__all__ = ["mcp", "mcp_tool"]
