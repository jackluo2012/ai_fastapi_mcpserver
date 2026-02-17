"""
日志模块单元测试
"""
import logging

import pytest
import structlog

from app.core.logging import configure_logging, get_logger


class TestLogging:
    """测试日志模块"""

    def test_configure_logging_creates_logger(self):
        """测试日志配置后可获取 logger"""
        configure_logging()
        logger = get_logger()
        assert logger is not None

    def test_get_logger_with_context(self):
        """测试带上下文参数获取 logger"""
        configure_logging()
        logger = get_logger(component="test")
        assert logger is not None

    def test_logger_context_binding_with_contextvars(self):
        """测试使用 contextvars 绑定日志上下文"""
        configure_logging()

        structlog.contextvars.bind_contextvars(
            request_id="test-123",
            path="/test",
        )

        context = structlog.contextvars.get_contextvars()
        assert context.get("request_id") == "test-123"
        assert context.get("path") == "/test"

        structlog.contextvars.clear_contextvars()

    def test_contextvars_clear(self):
        """测试清除 contextvars 上下文"""
        structlog.contextvars.bind_contextvars(request_id="to-clear")
        structlog.contextvars.clear_contextvars()

        context = structlog.contextvars.get_contextvars()
        assert "request_id" not in context
