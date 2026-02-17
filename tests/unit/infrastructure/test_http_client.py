"""
HTTP 客户端模块单元测试
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.utils.http_client import AsyncHttpClient


class TestAsyncHttpClient:
    """测试异步 HTTP 客户端"""

    @pytest.mark.asyncio
    async def test_client_start(self):
        """测试客户端启动"""
        client = AsyncHttpClient()
        assert client._client is None

        await client.start()
        assert client._client is not None

        await client.stop()

    @pytest.mark.asyncio
    async def test_client_stop(self):
        """测试客户端停止"""
        client = AsyncHttpClient()
        await client.start()
        assert client._client is not None

        await client.stop()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_client_stop_when_not_started(self):
        """测试未启动时停止不报错"""
        client = AsyncHttpClient()
        # 不应抛出异常
        await client.stop()

    @pytest.mark.asyncio
    async def test_get_requires_start(self):
        """测试未初始化时调用 get 抛出 RuntimeError"""
        client = AsyncHttpClient()
        with pytest.raises(RuntimeError, match="未初始化"):
            await client.get("https://example.com")

    @pytest.mark.asyncio
    async def test_post_requires_start(self):
        """测试未初始化时调用 post 抛出 RuntimeError"""
        client = AsyncHttpClient()
        with pytest.raises(RuntimeError):
            await client.post("https://example.com")

    @pytest.mark.asyncio
    async def test_get_success(self):
        """测试 GET 请求成功"""
        client = AsyncHttpClient()
        await client.start()
        try:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": "test"}
            mock_response.raise_for_status = MagicMock()

            with patch.object(
                client._client, "get", new_callable=AsyncMock, return_value=mock_response
            ):
                result = await client.get("https://example.com/api")
                assert result == {"data": "test"}
        finally:
            await client.stop()

    @pytest.mark.asyncio
    async def test_post_success(self):
        """测试 POST 请求成功"""
        client = AsyncHttpClient()
        await client.start()
        try:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"created": True}
            mock_response.raise_for_status = MagicMock()

            with patch.object(
                client._client, "post", new_callable=AsyncMock, return_value=mock_response
            ):
                result = await client.post("https://example.com/api", json={"key": "value"})
                assert result == {"created": True}
        finally:
            await client.stop()
