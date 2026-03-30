"""
邮件 MCP 工具
提供邮件列表查看、邮件详情查看、邮件发送三个 MCP 工具
"""

from typing import Annotated, Optional

from pydantic import Field

from app.core.context import require_user_id
from app.core.logging import get_logger
from app.mcp_server.app import mcp_tool
from app.services import imap_service, smtp_service
from app.services.user_store import user_store

logger = get_logger()


@mcp_tool(
    name="get_mail_list",
    description="""获取邮箱中的邮件列表。

功能描述：从指定邮箱文件夹中获取邮件列表，返回邮件的摘要信息。

触发时机：当需要查看邮箱中的邮件列表、浏览邮件概览、或搜索特定主题的邮件时使用。

典型示例：
- 查看收件箱中的最新20封邮件
- 搜索包含"会议"关键词的邮件
- 分页浏览邮件（使用offset和limit参数）

适用边界：
- 当前仅适用于qq、新浪、163邮箱""",
)
async def get_mail_list(
    email: Annotated[
        str,
        Field(
            description="""要查询的邮箱账号地址。可能从上下文或者长记忆中获取用户邮箱。示例：alice@qq.com、bob@163.com、charlie@sina.com""",
        ),
    ],
    folder: Annotated[
        str,
        Field(
            description="""可选参数，指定要查询的邮箱文件夹。默认是主文件夹INBOX。可通过用户的明确需求指定，没有指定就用默认的。示例：INBOX""",
            default="INBOX",
        ),
    ] = "INBOX",
    limit: Annotated[
        int,
        Field(
            description="""可选，每页返回的邮件条数。默认20，建议取值范围：1-100，示例：20、50、100""",
            default=20,
        ),
    ] = 20,
    offset: Annotated[
        int,
        Field(
            description="分页查询时的起始位置偏移量，用于跳过前面的邮件，与 limit 参数配合实现分页。第一页使用 offset=0，第二页使用 offset=limit，以此类推。",
            default=0,
        ),
    ] = 0,
    query: Annotated[
        Optional[str],
        Field(
            description="""搜索查询字符串，支持前缀协议指定搜索字段。

参数说明：用于在邮件中搜索的关键词，支持通过前缀指定搜索字段。

取值/边界描述：字符串类型，可选参数，默认值为 None。支持以下搜索协议格式：
- 无前缀：默认搜索主题，如 "会议"、"通知"
- subject:关键词 - 搜索主题，如 "subject:会议"
- from:发件人 - 搜索发件人地址，如 "from:alice@qq.com"、"from:@qq.com"
- to:收件人 - 搜索收件人地址，如 "to:bob@163.com"
- text:关键词 - 搜索标题或正文（更广泛），如 "text:重要"
- body:关键词 - 搜索正文内容，如 "body:报告"

示例：
- 会议（搜索主题包含"会议"）
- subject:会议（同上）
- from:alice@qq.com（搜索来自alice@qq.com的邮件）
- from:@qq.com（搜索来自QQ邮箱的邮件）
- text:重要（搜索标题或正文包含"重要"的邮件）
- body:报告（搜索正文包含"报告"的邮件）""",
            default=None,
        ),
    ] = None,
) -> dict:
    """获取邮箱中的邮件列表。

    Args:
        email: 邮箱地址（必须已通过 /api/v1/register 注册）
        folder: 邮箱文件夹，默认 INBOX
        limit: 每页数量，默认 20
        offset: 偏移量，默认 0
        query: 按主题搜索关键词
    """
    user_id = require_user_id()
    account = user_store.validate_access(user_id, email)
    mails = await imap_service.fetch_mail_list(
        email=account.email,
        passkey=account.passkey,
        folder=folder,
        limit=limit,
        offset=offset,
        query=query,
    )
    return {"total": len(mails), "offset": offset, "mails": mails}


@mcp_tool(
    name="get_mail_detail",
    description="""获取指定邮件的详细内容。

功能描述：根据邮件UID获取单封邮件的完整详细信息，包括正文、收件人、抄送人等。

获得目标：邮件的完整内容，包括纯文本正文、HTML正文、发件人、收件人、抄送人、主题、日期、附件列表等。

触发时机：当需要查看某封邮件的完整内容、阅读邮件正文、查看附件信息时使用。

典型示例：
- 查看UID为"123"的邮件详情
- 阅读收件箱中某封邮件的完整内容
- 获取邮件的附件列表信息
""",
)
async def get_mail_detail(
    email: Annotated[
        str,
        Field(
            description="""要查询的邮箱账号地址。从上下文中获取。示例：alice@qq.com、bob@163.com、charlie@sina.com""",
        ),
    ],
    mail_uid: Annotated[
        str,
        Field(
            description="""邮件的唯一标识符，用于定位要查询的具体邮件。先调用 get_mail_list 获取邮件列表，从返回结果中选择要查看详情的邮件的 uid 字段值。
示例：123、456、789（具体值取决于邮箱服务商）""",
        ),
    ],
    folder: Annotated[
        str,
        Field(
            description="指定邮件所在的邮箱文件夹，必须与 get_mail_list 查询时使用的文件夹一致，否则可能找不到邮件。",
            default="INBOX",
        ),
    ] = "INBOX",
) -> dict:
    """获取指定邮件的详细内容。

    Args:
        email: 邮箱地址（必须已通过 /api/v1/register 注册）
        mail_uid: 邮件 UID（从 get_mail_list 返回结果中获取）
        folder: 邮箱文件夹，默认 INBOX
    """
    user_id = require_user_id()
    account = user_store.validate_access(user_id, email)
    detail = await imap_service.fetch_mail_detail(
        email=account.email,
        passkey=account.passkey,
        mail_uid=mail_uid,
        folder=folder,
    )
    if detail is None:
        return {"error": f"未找到 UID 为 {mail_uid} 的邮件"}
    return detail


@mcp_tool(
    name="send_email",
    description="""发送邮件。

功能描述：通过SMTP服务器发送邮件，支持纯文本和HTML格式，自动检测正文格式。

获得目标：邮件发送结果，包括是否成功、发送到的邮箱地址、邮件主题等信息。

触发时机：当需要发送邮件、发送通知、发送报告或任何需要邮件通信的场景时使用。

典型示例：
- 发送一封主题为"会议通知"的纯文本邮件给alice@qq.com
- 发送包含HTML格式的邮件（如带格式的报表）
- 发送工作通知或提醒邮件

适用边界：
- 能做什么：发送纯文本邮件、发送HTML格式邮件
- 不能做什么：不能发送附件、不能设置抄送（CC）和密送（BCC）""",
)
async def send_mail(
    from_email: Annotated[
        str,
        Field(
            description="""发送邮件的邮箱账号，通常是从上下文中查找用户自己的邮箱。
示例：alice@qq.com、bob@163.com、charlie@sina.com""",
        ),
    ],
    to_email: Annotated[
        str,
        Field(
            description="接收邮件的目标邮箱地址，从上下文中用户要求明确告知的邮箱地址。",
        ),
    ],
    subject: Annotated[
        str,
        Field(
            description="""邮件的主题/标题，建议长度不超过200个字符。主题不能为空。
            根据用户指定或者根据邮件内容设置清晰、简洁的主题，便于收件人快速了解邮件内容。
            """,
        ),
    ],
    body: Annotated[
        str,
        Field(
            description="""邮件的正文内容，支持纯文本和HTML两种格式。如果正文包含HTML标签（如 <p>、<div>、<a> 等），系统会自动识别为HTML格式并发送HTML邮件；否则发送纯文本邮件。
示例：
- 纯文本：这是一封测试邮件，请查收。
- HTML：<h1>标题</h1><p>这是一封<strong>HTML格式</strong>的邮件。</p>""",
        ),
    ],
) -> dict:
    """发送邮件。

    Args:
        from_email: 发件人邮箱（必须已通过 /api/v1/register 注册）
        to_email: 收件人邮箱
        subject: 邮件主题
        body: 邮件正文，支持纯文本或 HTML
    """
    user_id = require_user_id()
    account = user_store.validate_access(user_id, from_email)
    return await smtp_service.send_email(
        from_email=account.email,
        passkey=account.passkey,
        to_email=to_email,
        subject=subject,
        body=body,
    )