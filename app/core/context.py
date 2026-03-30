"""
用户上下文模块
使用 contextvars 在异步调用链中传递 user_id
"""
from contextvars import ContextVar
from typing import Optional

_user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)

def set_user_id(uid: str) -> None:
    """在 transport 层调用，将 user_id 写入当前上下文。"""
    _user_id_var.set(uid)


def get_user_id() -> Optional[str]:
    """获取当前上下文中的 user_id，未设置时返回 None。"""
    return _user_id_var.get()


def require_user_id() -> str:
    """获取当前上下文中的 user_id，缺失则抛出 ValueError。"""
    uid = _user_id_var.get()
    if not uid:
        raise ValueError("缺少 X-User-Id 请求头，无法识别用户身份")
    return uid