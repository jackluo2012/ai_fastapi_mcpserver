"""
结构化日志配置模块
基于Structlog实现JSON格式日志输出和请求ID绑定

日志输出：
- stdout: 控制台输出（格式由 JSON_LOGS 配置控制）
- logs/app.log: 全量日志文件（RotatingFileHandler, 50MB * 10）
- logs/app.log.wf: WARNING 及以上级别日志（RotatingFileHandler, 50MB * 10）
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog.types import Processor

from app.core.config import get_settings

settings = get_settings()

# 日志目录：项目根目录/logs
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"


def configure_logging() -> None:
    """
    配置结构化日志系统
    设置JSON格式输出、请求ID绑定、文件日志分级输出
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 解析日志级别，无效时回退为 INFO
    log_level_name = settings.LOG_LEVEL.upper()
    log_level = getattr(logging, log_level_name, None)
    if not isinstance(log_level, int):
        log_level = logging.INFO

    # structlog 前置处理器链（enrichment阶段）
    shared_processors: list[Processor] = [
        # 合并 contextvars 上下文（request_id 等），必须在最前面
        structlog.contextvars.merge_contextvars,
        # 添加时间戳
        structlog.processors.TimeStamper(fmt="iso"),
        # 添加日志级别
        structlog.processors.add_log_level,
        # 添加堆栈信息
        structlog.processors.StackInfoRenderer(),
        # 格式化异常信息
        structlog.processors.format_exc_info,
        # 添加调用者信息
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
    ]

    # 配置 structlog：使用 stdlib logging 作为输出后端
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 根据配置选择控制台输出格式
    if settings.JSON_LOGS:
        console_renderer = structlog.processors.JSONRenderer()
    else:
        console_renderer = structlog.dev.ConsoleRenderer()

    # 控制台 formatter
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            console_renderer,
        ],
    )

    # 文件 formatter（始终使用 JSON，便于日志采集和分析）
    file_formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    # 配置 root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)

    # Handler 1: stdout 控制台输出
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(console_formatter)
    stdout_handler.setLevel(log_level)
    root_logger.addHandler(stdout_handler)

    # Handler 2: logs/app.log — 全量日志（带轮转：50MB * 10 份）
    app_log_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=50 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    app_log_handler.setFormatter(file_formatter)
    app_log_handler.setLevel(log_level)
    root_logger.addHandler(app_log_handler)

    # Handler 3: logs/app.log.wf — WARNING 及以上级别（带轮转：50MB * 10 份）
    wf_log_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "app.log.wf",
        maxBytes=50 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    wf_log_handler.setFormatter(file_formatter)
    wf_log_handler.setLevel(logging.WARNING)
    root_logger.addHandler(wf_log_handler)


def get_logger(**kwargs: Any) -> structlog.BoundLogger:
    """
    获取配置好的日志记录器
    可以传入初始上下文变量

    Args:
        **kwargs: 初始上下文变量

    Returns:
        structlog.BoundLogger: 配置好的日志记录器
    """
    return structlog.get_logger(**kwargs)


