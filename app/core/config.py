"""
核心配置模块
使用Pydantic Settings从环境变量加载配置，确保类型安全
"""
import json
from functools import lru_cache
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类，从环境变量加载配置"""

    # 项目基本信息
    PROJECT_NAME: str = Field(default="Enterprise MCP Server", description="项目名称")
    VERSION: str = Field(default="1.0.0", description="项目版本")
    API_V1_STR: str = Field(default="/api/v1", description="API版本前缀")

    # 安全配置
    MCP_API_KEY: str = Field(..., description="MCP API密钥，必须设置")
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        description="允许的Origin列表（CORS配置），支持 JSON 数组或逗号分隔字符串",
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """解析 ALLOWED_ORIGINS：支持 JSON 数组字符串或逗号分隔字符串，并禁止通配符 '*'。"""
        if isinstance(v, list):
            origins = v
        elif isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                try:
                    origins = json.loads(v)
                except json.JSONDecodeError:
                    origins = [o.strip() for o in v.split(",") if o.strip()]
            else:
                origins = [o.strip() for o in v.split(",") if o.strip()]
        else:
            origins = ["http://localhost:3000"]
        # 统一为字符串列表
        origins = [str(x).strip() for x in origins if str(x).strip()]
        if "*" in origins:
            raise ValueError("ALLOWED_ORIGINS 禁止使用通配符 '*'，请配置具体域名")
        return origins or ["http://localhost:3000"]

    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    JSON_LOGS: bool = Field(default=True, description="是否使用JSON格式日志")

    # Prometheus监控配置
    PROMETHEUS_ENABLED: bool = Field(default=True, description="是否启用Prometheus监控")

    # HTTP客户端配置
    HTTP_CLIENT_TIMEOUT: float = Field(default=30.0, description="HTTP客户端超时时间（秒）")
    HTTP_CLIENT_MAX_KEEPALIVE_CONNECTIONS: int = Field(
        default=50, description="HTTP客户端最大保持连接数"
    )
    HTTP_CLIENT_MAX_CONNECTIONS: int = Field(
        default=100, description="HTTP客户端最大连接数"
    )

    # 服务器配置
    HOST: str = Field(default="0.0.0.0", description="服务器监听地址")
    PORT: int = Field(default=8000, description="服务器监听端口")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    获取应用配置单例
    使用LRU缓存确保配置只加载一次

    Returns:
        Settings: 应用配置实例
    """
    return Settings()
