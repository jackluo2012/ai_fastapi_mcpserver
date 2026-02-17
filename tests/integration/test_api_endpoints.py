"""
API 端点集成测试
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestAPIEndpoints:
    """测试 API 端点"""

    def test_health_check(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data

    def test_health_check_response_structure(self, client: TestClient):
        """测试健康检查响应结构"""
        response = client.get("/health")
        data = response.json()

        assert isinstance(data, dict)
        assert "status" in data
        assert "version" in data
        assert "service" in data

    def test_docs_endpoint(self, client: TestClient):
        """测试 API 文档端点"""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint(self, client: TestClient):
        """测试 ReDoc 端点"""
        response = client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_metrics_endpoint(self, client: TestClient):
        """测试 Prometheus 指标端点"""
        response = client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        # 验证包含 Prometheus 指标格式
        assert "# HELP" in response.text or "mcp_tool_execution_total" in response.text

    def test_mcp_endpoint_requires_auth(self, client: TestClient):
        """测试 MCP 端点需要鉴权"""
        response = client.get("/mcp/")

        assert response.status_code == 401 or response.status_code == 403

    def test_mcp_endpoint_invalid_api_key(self, client: TestClient):
        """测试 MCP 端点无效 API Key"""
        response = client.get(
            "/mcp/",
            headers={"X-API-Key": "invalid-key"}
        )

        assert response.status_code == 403

    @pytest.mark.skip(reason="TestClient 与 MCP session_manager.run() 的 lifespan 不同步，需真实启动服务后测")
    def test_mcp_post_tools_list(self, client: TestClient, api_key: str):
        """测试 MCP 端点 POST tools/list"""
        response = client.post(
            "/mcp/",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
        )
        assert response.status_code == 200

    def test_request_id_header(self, client: TestClient):
        """测试 Request ID 响应头"""
        response = client.get("/health")

        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] is not None

    def test_custom_request_id(self, client: TestClient):
        """测试自定义 Request ID 透传"""
        custom_id = "custom-request-id-123"
        response = client.get(
            "/health",
            headers={"X-Request-ID": custom_id}
        )

        assert response.headers["X-Request-ID"] == custom_id
