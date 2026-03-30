"""
用户邮箱注册路由
提供邮箱账号的注册、移除和查询 HTTP 端点
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from app.core.logging import get_logger
from app.core.security import verify_api_key
from app.services.email_providers import get_provider_config
from app.services.user_store import user_store
logger = get_logger()

router = APIRouter(prefix="/api/v1", tags=["registration"])
class RegisterRequest(BaseModel):
    """注册请求体"""

    user_id: str
    email: EmailStr
    passkey: str
class RemoveRequest(BaseModel):
    """移除请求体"""

    user_id: str
    email: EmailStr
@router.post("/register")
async def register_account(
    req: RegisterRequest,
    _api_key: str = Depends(verify_api_key),
) -> dict:
    """注册或更新用户邮箱账号。

    需要 API Key 鉴权。邮箱域名必须在支持列表中。
    """
    # 校验邮箱域名是否受支持
    get_provider_config(req.email)
    print('get_provider_config success',req)
    await user_store.register_account(req.user_id, req.email, req.passkey)
    return {
        "success": True,
        "message": f"邮箱 {req.email} 已注册到用户 {req.user_id}",
    }
@router.delete("/register")
async def remove_account(
    req: RemoveRequest,
    _api_key: str = Depends(verify_api_key),
) -> dict:
    """移除用户邮箱账号。"""
    removed = await user_store.remove_account(req.user_id, req.email)
    if not removed:
        return {"success": False, "message": f"用户 {req.user_id} 未注册邮箱 {req.email}"}
    return {"success": True, "message": f"已移除邮箱 {req.email}"}

@router.get("/accounts/{user_id}")
async def list_accounts(
    user_id: str,
    _api_key: str = Depends(verify_api_key),
) -> dict:
    """列出用户已注册的所有邮箱地址。"""
    accounts = user_store.list_accounts(user_id)
    return {"user_id": user_id, "accounts": accounts}