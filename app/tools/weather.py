'''
天气查询工具模块
支持真实 API 调用和模拟数据两种模式
'''
import httpx
from app.core.logging import get_logger
from app.mcp_server.app import mcp_tool

logger = get_logger()

# 模拟天气数据（用于测试或网络不可用时）
MOCK_WEATHER_DATA = {
    "北京": {"temp_c": 22, "humidity": 45, "desc": "晴", "wind": "东北风 3级"},
    "上海": {"temp_c": 25, "humidity": 65, "desc": "多云", "wind": "东南风 2级"},
    "广州": {"temp_c": 28, "humidity": 75, "desc": "阵雨", "wind": "南风 3级"},
    "深圳": {"temp_c": 29, "humidity": 70, "desc": "阴", "wind": "东风 2级"},
    "beijing": {"temp_c": 22, "humidity": 45, "desc": "Sunny", "wind": "NE 3"},
    "shanghai": {"temp_c": 25, "humidity": 65, "desc": "Cloudy", "wind": "SE 2"},
    "newyork": {"temp_c": 15, "humidity": 55, "desc": "Clear", "wind": "NW 5"},
    "london": {"temp_c": 12, "humidity": 80, "desc": "Rain", "wind": "W 4"},
}

@mcp_tool(
    name="get_weather",
    description="查询指定城市的天气信息（支持中英文城市名）",
)
async def get_weather(city: str, unit: str = "celsius", use_mock: bool = False) -> dict:
    """
    查询天气信息

    Args:
        city: 城市名称（支持中文，如"北京"或"Beijing"）
        unit: 温度单位，celsius（摄氏度）或 fahrenheit（华氏度）
        use_mock: 是否使用模拟数据（默认 false，使用真实 API）

    Returns:
        dict: 包含温度、天气状况、位置等信息
    """
    logger.info("querying_weather", city=city, unit=unit, use_mock=use_mock)

    # 如果指定使用模拟数据，或城市在模拟数据中，则返回模拟数据
    city_lower = city.lower()
    if use_mock or city_lower in MOCK_WEATHER_DATA or city in MOCK_WEATHER_DATA:
        mock_data = MOCK_WEATHER_DATA.get(city) or MOCK_WEATHER_DATA.get(city_lower, {
            "temp_c": 20,
            "humidity": 50,
            "desc": "晴朗",
            "wind": "微风"
        })

        temp_c = mock_data["temp_c"]
        temp_f = int(temp_c * 9 / 5 + 32)

        if unit == "fahrenheit":
            temperature = f"{temp_f}°F"
        else:
            temperature = f"{temp_c}°C"

        result = {
            "city": city,
            "temperature": temperature,
            "temp_celsius": temp_c,
            "temp_fahrenheit": temp_f,
            "humidity": f"{mock_data['humidity']}%",
            "description": mock_data["desc"],
            "wind_speed": mock_data["wind"],
            "data_source": "mock"
        }

        logger.info("weather_mock_success", city=city, temp=temperature)
        return result

    # 使用真实的 wttr.in API
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"https://wttr.in/{city}?format=j1"
            logger.info("weather_api_request", url=url)

            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            current = data.get("current_condition", [{}])[0]
            temp_c = int(current.get("temp_C", 0))
            temp_f = int(current.get("temp_F", 0))

            if unit == "fahrenheit":
                temperature = f"{temp_f}°F"
            else:
                temperature = f"{temp_c}°C"

            result = {
                "city": city,
                "temperature": temperature,
                "temp_celsius": temp_c,
                "temp_fahrenheit": temp_f,
                "humidity": f"{current.get('humidity', 'N/A')}%",
                "description": current.get("weatherDesc", [{}])[0].get("value", "未知"),
                "wind_speed": f"{current.get('windspeedKmph', 'N/A')} km/h",
                "wind_direction": current.get("winddir16Point", "N/A"),
                "feels_like": f"{current.get('FeelsLikeC', 'N/A')}°C",
                "data_source": "wttr.in"
            }

            logger.info("weather_api_success", city=city, temp=temperature)
            return result

    except httpx.HTTPStatusError as e:
        logger.error("weather_api_error", status_code=e.response.status_code, city=city)
        raise ValueError(f"天气API返回错误状态码: {e.response.status_code}")

    except httpx.RequestError as e:
        logger.error("weather_network_error", error=str(e), city=city)
        # 网络错误时，降级到模拟数据
        logger.warning("weather_fallback_to_mock", city=city)
        return await get_weather(city=city, unit=unit, use_mock=True)

    except Exception as e:
        logger.exception("weather_unexpected_error", city=city, error=str(e))
        raise ValueError(f"获取天气信息时发生错误: {str(e)}")