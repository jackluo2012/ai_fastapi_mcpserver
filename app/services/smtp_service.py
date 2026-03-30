"""
SMTP 邮件发送服务
使用 aiosmtplib 原生异步发送邮件
"""
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.email_providers import get_provider_config

logger = get_logger()

_HTML_TAG_RE = re.compile(r"<[a-zA-Z][^>]*>")

def _detect_content_type(body: str) -> str:
    """自动检测 body 内容类型：含 HTML 标签则返回 'html'，否则 'plain'。"""
    if _HTML_TAG_RE.search(body):
        return "html"
    return "plain"

async def send_email(
    from_email: str,
    passkey: str,
    to_email: str,
    subject: str,
    body: str,
    content_type: str = "auto",
) -> dict:
    """发送邮件。

    Args:
        from_email: 发件人邮箱
        passkey: 授权码
        to_email: 收件人邮箱
        subject: 邮件主题
        body: 邮件正文
        content_type: 内容类型，'plain'/'html'/'auto'（自动检测）

    Returns:
        发送结果字典
    """
    settings = get_settings()
    provider = get_provider_config(from_email)

    if content_type == "auto":
        content_type = _detect_content_type(body)

    # 构建 MIME 消息
    msg = MIMEMultipart("alternative")
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, content_type, "utf-8"))

    logger.info(
        "smtp_send",
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        content_type=content_type,
    )

    await aiosmtplib.send(
        msg,
        hostname=provider.smtp_host,
        port=provider.smtp_port,
        username=from_email,
        password=passkey,
        use_tls=provider.smtp_use_tls,
        timeout=settings.SMTP_TIMEOUT,
    )

    logger.info("smtp_send_success", from_email=from_email, to_email=to_email)
    return {
        "success": True,
        "from": from_email,
        "to": to_email,
        "subject": subject,
    }