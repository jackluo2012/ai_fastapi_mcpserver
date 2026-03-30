"""
邮箱提供商配置
按域名后缀映射到对应的 IMAP/SMTP 服务器地址
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class EmailProviderConfig:
    """邮箱提供商服务器配置"""

    imap_host: str
    imap_port: int  # 993 (SSL)
    smtp_host: str
    smtp_port: int  # 465 (SSL) 或 587 (STARTTLS)
    smtp_use_tls: bool  # True=直接TLS(465), False=STARTTLS(587)


PROVIDER_MAP: dict[str, EmailProviderConfig] = {
    "qq.com": EmailProviderConfig("imap.qq.com", 993, "smtp.qq.com", 465, True),
    "sina.com": EmailProviderConfig("imap.sina.com", 993, "smtp.sina.com", 465, True),
    "sina.cn": EmailProviderConfig("imap.sina.com", 993, "smtp.sina.com", 465, True),
    "163.com": EmailProviderConfig("imap.163.com", 993, "smtp.163.com", 465, True),
}

def get_provider_config(email: str) -> EmailProviderConfig:
    """按邮箱域名后缀查找提供商配置。

    Args:
        email: 完整邮箱地址

    Returns:
        EmailProviderConfig: 对应提供商的服务器配置

    Raises:
        ValueError: 邮箱域名不在支持列表中
    """
    if "@" not in email:
        raise ValueError(f"无效的邮箱地址: {email}")
    domain = email.rsplit("@", 1)[1].lower()
    config = PROVIDER_MAP.get(domain)
    if not config:
        supported = ", ".join(sorted(PROVIDER_MAP.keys()))
        raise ValueError(f"不支持的邮箱域名: {domain}，当前支持: {supported}")
    return config