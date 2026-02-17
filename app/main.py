"""
主应用入口模块
整合所有组件，创建FastAPI应用并配置中间件、异常处理和路由
"""
import asyncio
import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import get_settings
from app.core.exceptions import (
    MCPException,
    general_exception_handler,
    mcp_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging, get_logger
from app.core.security import verify_origin
from app.mcp_server.app import mcp
from app.mcp_server.transport import create_protected_mcp_app
from app.utils.http_client import http_client

# 配置日志系统
configure_logging()
logger = get_logger()

# 获取配置
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    在应用启动时初始化资源，在关闭时清理资源。
    MCP 挂载为子应用时其 lifespan 不会自动执行，需在此处运行 session_manager.run()。
    """
    logger.info("application_starting")
    async with mcp.session_manager.run():
        await http_client.start()
        logger.info("application_started")
        yield
        logger.info("application_shutting_down")
        # 优雅关闭：等待进行中的请求完成
        logger.info("draining_in_flight_requests", grace_period_seconds=5)
        await asyncio.sleep(5)
        await http_client.stop()
    logger.info("application_shutdown_complete")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI文档
    redoc_url="/redoc",  # ReDoc文档
    openapi_url="/openapi.json",  # OpenAPI JSON schema
)

# 配置CORS中间件
# 严格限制允许的Origin，禁止使用通配符
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],  # 暴露MCP Session ID头部
)

# 注册全局异常处理器
app.add_exception_handler(MCPException, mcp_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """
    请求ID与耗时中间件
    为每个请求生成唯一的Request ID（或透传客户端传入的），用于全链路追踪。
    同时记录请求耗时 latency_ms。
    """
    # 支持客户端透传 X-Request-ID，否则生成新的
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    # 使用 contextvars 绑定 request_id，确保整个请求链路的日志都包含此字段
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    start = time.time()
    response = await call_next(request)
    latency_ms = round((time.time() - start) * 1000, 2)

    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        latency_ms=latency_ms,
    )

    # 将请求ID添加到响应头
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def origin_verification_middleware(request: Request, call_next):
    """
    Origin验证中间件
    验证请求的Origin头部，防止DNS重绑定攻击
    """
    # 跳过健康检查、指标、文档、根路径及 MCP 端点（MCP 由 API Key 鉴权，且多为程序化调用无 Origin）
    if request.url.path in [
        "/",
        "/health",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    ] or request.url.path.startswith("/mcp"):
        return await call_next(request)

    try:
        verify_origin(request)
    except Exception as e:
        logger.warning("origin_verification_failed", error=str(e), path=request.url.path)
        # 让异常处理器处理
        raise

    return await call_next(request)


# 配置Prometheus指标导出
if settings.PROMETHEUS_ENABLED:
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
    logger.info("prometheus_metrics_enabled", endpoint="/metrics")


# 挂载受保护的MCP Streamable HTTP应用
# 注意：Starlette 会对 POST /mcp 返回 307 重定向到 /mcp/，客户端请直接请求 /mcp/（带末尾斜杠）
protected_mcp_app = create_protected_mcp_app()
app.mount("/mcp", protected_mcp_app)
logger.info("mcp_endpoint_mounted", path="/mcp")


@app.get("/health")
async def health_check() -> dict:
    """
    健康检查端点
    用于Kubernetes liveness和readiness探针
    """
    return {
        "status": "ok",
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME,
    }


@app.get("/")
async def root() -> dict:
    """
    根端点
    返回API基本信息
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "mcp_endpoint": "/mcp",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_config=None,  # 使用我们自己的日志配置
    )
