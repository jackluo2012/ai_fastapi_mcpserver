import pytest
from unittest.mock import patch, AsyncMock

from app.tools.weather import get_weather

@pytest.mark.asyncio
async def test_get_weather():
    mock_data = {"temp": 22.5, "humidity": 65, "description": "晴"}
    # Mock http_client instance and its get method
    mock_get = AsyncMock(return_value=mock_data)
    with patch("app.utils.http_client.http_client.get", mock_get):
        result = await get_weather("北京")

        assert result["city"] == "北京"
        assert result["temperature"] == 22.5
        assert result["humidity"] == 65
        assert result["description"] == "晴"
        mock_get.assert_called_once_with(
            "https://api.weather.example.com/v1/current?city=北京&unit=celsius"
        )