"""
安全模块测试
"""
import os

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from starlette.datastructures import Headers

from app.core.security import verify_api_key_asgi, verify_origin
from app.main import app


@pytest.mark.asyncio
async def test_verify_api_key_asgi_valid():
    """测试有效的API Key验证"""
    scope = {"type": "http"}
    headers = {b"x-api-key": b"test-api-key-12345"}

    result = await verify_api_key_asgi(scope, headers)
    assert result is True


@pytest.mark.asyncio
async def test_verify_api_key_asgi_invalid():
    """测试无效的API Key验证"""
    scope = {"type": "http"}
    headers = {b"x-api-key": b"wrong-key"}

    result = await verify_api_key_asgi(scope, headers)
    assert result is False


@pytest.mark.asyncio
async def test_verify_api_key_asgi_bearer():
    """测试 Bearer Token 格式的API Key验证"""
    scope = {"type": "http"}
    headers = {b"authorization": b"Bearer test-api-key-12345"}

    result = await verify_api_key_asgi(scope, headers)
    assert result is True


@pytest.mark.asyncio
async def test_verify_api_key_asgi_missing():
    """测试缺少API Key"""
    scope = {"type": "http"}
    headers = {}

    result = await verify_api_key_asgi(scope, headers)
    assert result is False


def test_verify_origin_allowed():
    """测试允许的Origin验证"""
    headers = Headers({"origin": "http://localhost:3000"})
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": headers.raw,
        }
    )

    # 应该不抛出异常
    verify_origin(request)


def test_verify_origin_not_allowed():
    """测试不允许的Origin验证"""
    headers = Headers({"origin": "http://evil.com"})
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": headers.raw,
        }
    )

    from app.core.exceptions import AuthorizationError

    with pytest.raises(AuthorizationError):
        verify_origin(request)


def test_verify_origin_no_header():
    """测试无Origin头部（直接API调用）跳过验证"""
    headers = Headers({})
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": headers.raw,
        }
    )

    # 无Origin头部应该跳过验证，不抛出异常
    verify_origin(request)


def test_health_endpoint_no_auth(client: TestClient):
    """测试健康检查端点不需要认证"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_mcp_endpoint_requires_auth(client: TestClient):
    """测试MCP端点需要认证"""
    # 不带API Key的请求应该被拒绝
    response = client.post("/mcp/", json={"jsonrpc": "2.0", "method": "initialize", "id": 1})
    assert response.status_code == 403


def test_mcp_endpoint_with_auth(client: TestClient):
    """测试带认证的MCP端点"""
    headers = {"X-API-Key": "test-api-key-12345"}
    # 注意：实际的MCP请求需要正确的JSON-RPC格式
    # 这里只是测试鉴权是否通过
    response = client.post("/mcp/", json={}, headers=headers)
    # 可能返回400（格式错误）而不是403（未授权），说明鉴权通过
    assert response.status_code != 403
