"""
Pytest配置和共享fixture
"""
import os

# 在导入 app 前设置测试环境变量，避免 get_settings() 在模块加载时因缺少 MCP_API_KEY 失败
os.environ.setdefault("MCP_API_KEY", "test-api-key-12345")
os.environ.setdefault(
    "ALLOWED_ORIGINS",
    '["http://localhost:3000","http://test.example.com"]',
)
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("JSON_LOGS", "false")
os.environ.setdefault("PROMETHEUS_ENABLED", "true")

from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app


@pytest.fixture(scope="session")
def test_settings() -> dict:
    """
    测试配置fixture
    返回当前测试环境变量对应的配置（用于断言等）

    Returns:
        dict: 测试配置字典
    """
    return {
        "MCP_API_KEY": os.environ.get("MCP_API_KEY", "test-api-key-12345"),
        "ALLOWED_ORIGINS": ["http://localhost:3000", "http://test.example.com"],
    }


@pytest.fixture
def api_key(test_settings: dict) -> str:
    """MCP API Key，与 conftest 中 MCP_API_KEY 一致。"""
    return test_settings["MCP_API_KEY"]


@pytest.fixture
def client(test_settings: dict) -> TestClient:
    """
    同步测试客户端fixture

    Args:
        test_settings: 测试配置

    Returns:
        TestClient: FastAPI测试客户端
    """
    return TestClient(app)


@pytest.fixture
async def async_client(test_settings: dict) -> AsyncGenerator[AsyncClient, None]:
    """
    异步测试客户端fixture

    Args:
        test_settings: 测试配置

    Yields:
        AsyncClient: 异步HTTP客户端
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
