"""
IMAP 邮件读取服务
使用 imap_tools 通过 asyncio.to_thread 包装同步操作
"""
import asyncio
from typing import Optional

from imap_tools import MailBox, AND, OR, MailMessageFlags

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.email_providers import get_provider_config

logger = get_logger()

def _parse_search_query(query: str):
    """
    解析搜索查询字符串，支持前缀协议。

    支持的搜索协议：
    - subject:关键词 - 搜索主题
    - from:发件人 - 搜索发件人
    - to:收件人 - 搜索收件人
    - text:关键词 - 搜索标题或正文（更广泛）
    - body:关键词 - 搜索正文内容
    - 无前缀 - 默认搜索主题（向后兼容）

    Args:
        query: 搜索查询字符串

    Returns:
        imap_tools 搜索条件对象
    """
    if not query:
        return "ALL"

    query = query.strip()

    # 检查是否有前缀
    if ":" in query:
        parts = query.split(":", 1)
        if len(parts) == 2:
            prefix = parts[0].strip().lower()
            value = parts[1].strip()

            if not value:
                # 如果前缀后没有值，记录警告并返回所有邮件
                logger.warning("empty_search_value", prefix=prefix, query=query)
                return "ALL"

            if prefix == "subject":
                return AND(subject=value)
            elif prefix == "from":
                return AND(from_=value)
            elif prefix == "to":
                return AND(to=value)
            elif prefix == "text":
                return AND(text=value)
            elif prefix == "body":
                return AND(body=value)
            else:
                # 未知前缀，回退到默认搜索主题
                logger.warning("unknown_search_prefix", prefix=prefix, query=query)
                return AND(subject=query)

    # 无前缀，默认搜索主题（向后兼容）
    return AND(subject=query)

def _connect_and_fetch_list(
    imap_host: str,
    imap_port: int,
    email: str,
    passkey: str,
    folder: str,
    limit: int,
    offset: int,
    query: Optional[str],
    timeout: int,
) -> list[dict]:
    """同步：连接 IMAP 并获取邮件列表（仅 headers）。"""
    criteria = _parse_search_query(query) if query else "ALL"

    with MailBox(imap_host, imap_port, timeout=timeout).login(
        email, passkey, initial_folder=folder
    ) as mailbox:
        # 获取邮件，reverse=True 最新在前，headers_only=True 避免下载正文
        messages = list(
            mailbox.fetch(
                criteria,
                reverse=True,
                headers_only=True,
                limit=offset + limit,
                mark_seen=False,
            )
        )
        # 手动分页
        page = messages[offset : offset + limit]
        return [
            {
                "uid": msg.uid,
                "subject": msg.subject,
                "from": msg.from_,
                "to": list(msg.to),
                "date": msg.date_str,
                "seen": MailMessageFlags.SEEN in msg.flags,
            }
            for msg in page
        ]
def _connect_and_fetch_detail(
    imap_host: str,
    imap_port: int,
    email: str,
    passkey: str,
    mail_uid: str,
    folder: str,
    timeout: int,
) -> Optional[dict]:
    """同步：连接 IMAP 并获取单封邮件详情。"""
    with MailBox(imap_host, imap_port, timeout=timeout).login(
        email, passkey, initial_folder=folder
    ) as mailbox:
        # QQ Mail 的 IMAP 对 UID SEARCH 返回 >= 指定 UID 的所有邮件
        # 因此需要在 Python 侧精确匹配
        target = None
        for msg in mailbox.fetch(AND(uid=mail_uid), mark_seen=False):
            if msg.uid == mail_uid:
                target = msg
                break
        if target is None:
            return None
        msg = target
        attachments = [
            {
                "filename": att.filename,
                "content_type": att.content_type,
                "size": len(att.payload),
            }
            for att in msg.attachments
        ]
        return {
            "uid": msg.uid,
            "subject": msg.subject,
            "from": msg.from_,
            "to": list(msg.to),
            "cc": list(msg.cc),
            "date": msg.date_str,
            "text_body": msg.text,
            "html_body": msg.html,
            "attachments": attachments,
        }


async def fetch_mail_list(
    email: str,
    passkey: str,
    folder: str = "INBOX",
    limit: int = 20,
    offset: int = 0,
    query: Optional[str] = None,
) -> list[dict]:
    """异步获取邮件列表。

    Args:
        email: 邮箱地址
        passkey: 授权码
        folder: 邮箱文件夹
        limit: 每页数量
        offset: 偏移量
        query: 搜索关键词，支持前缀协议（见 _parse_search_query 函数说明）

    Returns:
        邮件摘要列表
    """
    settings = get_settings()
    provider = get_provider_config(email)
    logger.info(
        "imap_fetch_list",
        email=email,
        folder=folder,
        limit=limit,
        offset=offset,
        query=query,
    )
    return await asyncio.to_thread(
        _connect_and_fetch_list,
        provider.imap_host,
        provider.imap_port,
        email,
        passkey,
        folder,
        limit,
        offset,
        query,
        settings.IMAP_TIMEOUT,
    )


async def fetch_mail_detail(
    email: str,
    passkey: str,
    mail_uid: str,
    folder: str = "INBOX",
) -> Optional[dict]:
    """异步获取单封邮件详情。

    Args:
        email: 邮箱地址
        passkey: 授权码
        mail_uid: 邮件 UID
        folder: 邮箱文件夹

    Returns:
        邮件详情字典，未找到时返回 None
    """
    settings = get_settings()
    provider = get_provider_config(email)
    logger.info("imap_fetch_detail", email=email, mail_uid=mail_uid, folder=folder)
    return await asyncio.to_thread(
        _connect_and_fetch_detail,
        provider.imap_host,
        provider.imap_port,
        email,
        passkey,
        mail_uid,
        folder,
        settings.IMAP_TIMEOUT,
    )