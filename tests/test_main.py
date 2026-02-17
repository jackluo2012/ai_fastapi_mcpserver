"""
主应用测试
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_root_endpoint(client: TestClient):
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "mcp_endpoint" in data


def test_health_endpoint(client: TestClient):
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_metrics_endpoint(client: TestClient):
    """测试Prometheus指标端点"""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Prometheus指标应该是文本格式
    assert "text/plain" in response.headers.get("content-type", "")


def test_docs_endpoint(client: TestClient):
    """测试Swagger文档端点"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_endpoint(client: TestClient):
    """测试OpenAPI schema端点"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
