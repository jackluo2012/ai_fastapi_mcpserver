"""
配置模块测试
"""
import os

import pytest

from app.core.config import Settings, get_settings


def test_settings_load_from_env():
    """测试从环境变量加载配置"""
    os.environ["MCP_API_KEY"] = "test-key"
    os.environ["ALLOWED_ORIGINS"] = '["http://localhost:3000"]'

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.MCP_API_KEY == "test-key"
    assert "http://localhost:3000" in settings.ALLOWED_ORIGINS

    # 恢复测试环境值
    os.environ["MCP_API_KEY"] = "test-api-key-12345"
    os.environ["ALLOWED_ORIGINS"] = '["http://localhost:3000","http://test.example.com"]'
    get_settings.cache_clear()


def test_settings_required_api_key(monkeypatch):
    """测试 MCP_API_KEY 是必需字段"""
    # 彻底移除环境变量，确保 Settings 无法加载
    monkeypatch.delenv("MCP_API_KEY", raising=False)
    get_settings.cache_clear()

    with pytest.raises(Exception):
        Settings(_env_file=None)

    # 恢复
    monkeypatch.setenv("MCP_API_KEY", "test-api-key-12345")
    get_settings.cache_clear()


def test_settings_wildcard_origin_rejected():
    """测试通配符 * 被拒绝"""
    with pytest.raises(ValueError, match="禁止使用通配符"):
        Settings(
            _env_file=None,
            MCP_API_KEY="test-key",
            ALLOWED_ORIGINS=["*"],
        )


def test_settings_caching():
    """测试配置缓存功能"""
    os.environ["MCP_API_KEY"] = "test-key-1"
    get_settings.cache_clear()
    settings1 = get_settings()

    os.environ["MCP_API_KEY"] = "test-key-2"
    # 由于缓存，应该返回相同的实例
    settings2 = get_settings()

    assert settings1 is settings2

    # 恢复测试环境值
    os.environ["MCP_API_KEY"] = "test-api-key-12345"
    get_settings.cache_clear()


def test_settings_json_array_origins():
    """测试 JSON 数组格式的 ALLOWED_ORIGINS"""
    os.environ["MCP_API_KEY"] = "test-key"
    os.environ["ALLOWED_ORIGINS"] = '["http://localhost:3000","http://example.com"]'

    get_settings.cache_clear()
    settings = get_settings()

    assert "http://localhost:3000" in settings.ALLOWED_ORIGINS
    assert "http://example.com" in settings.ALLOWED_ORIGINS

    # 恢复测试环境值
    os.environ["MCP_API_KEY"] = "test-api-key-12345"
    os.environ["ALLOWED_ORIGINS"] = '["http://localhost:3000","http://test.example.com"]'
    get_settings.cache_clear()


def test_parse_allowed_origins_validator():
    """测试 ALLOWED_ORIGINS 验证器直接处理各种格式"""
    from app.core.config import Settings

    # 测试 list 输入
    result = Settings.parse_allowed_origins(["http://a.com", "http://b.com"])
    assert result == ["http://a.com", "http://b.com"]

    # 测试 JSON 字符串输入
    result = Settings.parse_allowed_origins('["http://a.com","http://b.com"]')
    assert result == ["http://a.com", "http://b.com"]

    # 测试逗号分隔字符串输入
    result = Settings.parse_allowed_origins("http://a.com,http://b.com")
    assert result == ["http://a.com", "http://b.com"]

    # 测试通配符拒绝
    with pytest.raises(ValueError, match="禁止使用通配符"):
        Settings.parse_allowed_origins(["*"])
