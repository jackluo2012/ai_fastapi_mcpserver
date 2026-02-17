"""
异步HTTP客户端模块
封装httpx.AsyncClient，提供连接池管理和自动重试功能
"""
import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger()
settings = get_settings()


class AsyncHttpClient:
    """
    异步HTTP客户端
    封装httpx.AsyncClient，提供连接池管理和自动重试功能
    """

    def __init__(self) -> None:
        """初始化HTTP客户端（延迟创建连接池）"""
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        """
        启动HTTP客户端
        创建连接池，应在应用启动时调用
        """
        self._client = httpx.AsyncClient(
            timeout=settings.HTTP_CLIENT_TIMEOUT,
            limits=httpx.Limits(
                max_keepalive_connections=settings.HTTP_CLIENT_MAX_KEEPALIVE_CONNECTIONS,
                max_connections=settings.HTTP_CLIENT_MAX_CONNECTIONS,
            ),
        )
        logger.info(
            "http_client_started",
            timeout=settings.HTTP_CLIENT_TIMEOUT,
            max_keepalive_connections=settings.HTTP_CLIENT_MAX_KEEPALIVE_CONNECTIONS,
            max_connections=settings.HTTP_CLIENT_MAX_CONNECTIONS,
        )

    async def stop(self) -> None:
        """
        停止HTTP客户端
        关闭连接池，应在应用关闭时调用
        """
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("http_client_stopped")

    def _ensure_client(self) -> httpx.AsyncClient:
        """
        确保客户端已初始化

        Returns:
            httpx.AsyncClient: HTTP客户端实例

        Raises:
            RuntimeError: 当客户端未初始化时抛出
        """
        if not self._client:
            raise RuntimeError("HTTP客户端未初始化，请先调用start()方法")
        return self._client

    @retry(
        stop=stop_after_attempt(3),  # 最多重试3次
        wait=wait_exponential(multiplier=1, min=2, max=10),  # 指数退避：2s, 4s, 8s
        retry=retry_if_exception_type(
            (
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.ConnectError,
                httpx.NetworkError,
            )
        ),  # 仅对网络相关异常重试
        reraise=True,  # 重试失败后抛出原始异常
    )
    async def get(self, url: str, **kwargs: dict) -> dict:
        """
        发送GET请求
        自动重试网络错误

        Args:
            url: 请求URL
            **kwargs: httpx.get的其他参数

        Returns:
            dict: JSON响应体

        Raises:
            httpx.HTTPStatusError: 当HTTP状态码表示错误时
            httpx.RequestError: 当请求失败时
        """
        client = self._ensure_client()
        try:
            response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "http_get_failed",
                url=url,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("http_get_request_error", url=url, error=str(e))
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.ConnectError,
                httpx.NetworkError,
            )
        ),
        reraise=True,
    )
    async def post(self, url: str, **kwargs: dict) -> dict:
        """
        发送POST请求
        自动重试网络错误

        Args:
            url: 请求URL
            **kwargs: httpx.post的其他参数

        Returns:
            dict: JSON响应体

        Raises:
            httpx.HTTPStatusError: 当HTTP状态码表示错误时
            httpx.RequestError: 当请求失败时
        """
        client = self._ensure_client()
        try:
            response = await client.post(url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "http_post_failed",
                url=url,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error("http_post_request_error", url=url, error=str(e))
            raise

    async def request(self, method: str, url: str, **kwargs: dict) -> httpx.Response:
        """
        发送通用HTTP请求
        不自动解析JSON，返回原始Response对象

        Args:
            method: HTTP方法（GET, POST等）
            url: 请求URL
            **kwargs: httpx.request的其他参数

        Returns:
            httpx.Response: HTTP响应对象

        Raises:
            httpx.HTTPStatusError: 当HTTP状态码表示错误时
            httpx.RequestError: 当请求失败时
        """
        client = self._ensure_client()
        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            logger.error(
                "http_request_failed",
                method=method,
                url=url,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise
        except httpx.RequestError as e:
            logger.error(
                "http_request_error",
                method=method,
                url=url,
                error=str(e),
            )
            raise


# 全局单例HTTP客户端实例
# 在应用启动时通过lifespan事件初始化
http_client = AsyncHttpClient()
