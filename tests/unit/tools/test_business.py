"""
系统工具单元测试
"""
import pytest

from app.tools.system import get_server_info


class TestSystemTools:
    """测试系统工具"""

    @pytest.mark.asyncio
    async def test_get_server_info(self):
        """测试获取服务器信息"""
        result = await get_server_info()

        assert "project_name" in result
        assert "version" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_get_server_info_types(self):
        """测试服务器信息字段类型"""
        result = await get_server_info()

        assert isinstance(result["project_name"], str)
        assert isinstance(result["version"], str)
        assert isinstance(result["timestamp"], str)

    @pytest.mark.asyncio
    async def test_get_server_info_timestamp_format(self):
        """测试服务器信息时间戳为 ISO 格式"""
        result = await get_server_info()
        timestamp = result["timestamp"]

        # ISO 格式应包含 T 分隔符
        assert "T" in timestamp
