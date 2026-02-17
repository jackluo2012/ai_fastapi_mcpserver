"""
工具模块测试
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.tools import demo, system


@pytest.mark.asyncio
async def test_hello_world():
    """测试Hello World工具"""
    result = await demo.hello_world("Test")
    assert "Hello" in result
    assert "Test" in result


@pytest.mark.asyncio
async def test_hello_world_default():
    """测试Hello World工具默认参数"""
    result = await demo.hello_world()
    assert "World" in result


@pytest.mark.asyncio
async def test_echo():
    """测试回显工具"""
    result = await demo.echo("test message")
    assert result == "test message"


@pytest.mark.asyncio
async def test_get_server_info():
    """测试获取服务器信息工具"""
    result = await system.get_server_info()
    assert "project_name" in result
    assert "version" in result
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_fetch_external_data_success():
    """测试获取外部数据工具成功场景"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    mock_response.raise_for_status = MagicMock()

    with patch("app.utils.http_client.http_client._client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_response)
        result = await system.fetch_external_data("https://api.example.com/data")
        assert "data" in result
        assert result["data"] == "test"


@pytest.mark.asyncio
async def test_fetch_external_data_failure():
    """测试获取外部数据工具失败场景"""
    import httpx

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error",
        request=MagicMock(),
        response=mock_response,
    )

    with patch("app.utils.http_client.http_client._client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_response)
        with pytest.raises(httpx.HTTPStatusError):
            await system.fetch_external_data("https://api.example.com/data")
