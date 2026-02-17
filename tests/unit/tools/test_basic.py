"""
基础工具单元测试
"""
import pytest

from app.tools.demo import hello_world, echo


class TestBasicTools:
    """测试基础工具"""

    @pytest.mark.asyncio
    async def test_hello_world_default(self):
        """测试 HelloWorld 默认参数"""
        result = await hello_world()
        assert "Hello, World!" in result
        assert "Enterprise MCP Server is running." in result

    @pytest.mark.asyncio
    async def test_hello_world_custom_name(self):
        """测试 HelloWorld 自定义名称"""
        result = await hello_world(name="Alice")
        assert "Hello, Alice!" in result
        assert "Enterprise MCP Server is running." in result

    @pytest.mark.asyncio
    async def test_hello_world_returns_string(self):
        """测试 HelloWorld 返回字符串类型"""
        result = await hello_world(name="Bob")
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_echo_returns_input(self):
        """测试 Echo 工具返回输入文本"""
        result = await echo(text="test message")
        assert result == "test message"

    @pytest.mark.asyncio
    async def test_echo_empty_string(self):
        """测试 Echo 工具空字符串"""
        result = await echo(text="")
        assert result == ""
