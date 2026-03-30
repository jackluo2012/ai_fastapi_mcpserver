"""
加密用户配置存储
使用 Fernet 对称加密保存用户邮箱账号信息到磁盘
"""
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger()


@dataclass
class EmailAccount:
    """用户邮箱账号"""

    email: str
    passkey: str


class UserStore:
    """加密用户配置存储，管理用户邮箱账号的增删查和持久化。"""

    def __init__(self) -> None:
        self._users: dict[str, list[EmailAccount]] = {}
        self._fernet: Optional[Fernet] = None
        self._lock = asyncio.Lock()
        self._store_path: Optional[Path] = None

    async def initialize(self) -> None:
        """初始化存储：加载加密密钥，从磁盘读取已有数据。"""
        settings = get_settings()
        key = settings.USER_STORE_ENCRYPTION_KEY
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        self._store_path = Path(settings.USER_STORE_PATH)

        if self._store_path.exists():
            encrypted_data = self._store_path.read_bytes()
            decrypted = self._fernet.decrypt(encrypted_data)
            raw: dict = json.loads(decrypted)
            for user_id, info in raw.items():
                self._users[user_id] = [
                    EmailAccount(email=acc["email"], passkey=acc["passkey"])
                    for acc in info["accounts"]
                ]
            logger.info("user_store_loaded", user_count=len(self._users))
        else:
            logger.info("user_store_empty", path=str(self._store_path))

    async def _persist(self) -> None:
        """将当前数据加密写入磁盘。调用前应持有 _lock。"""
        raw: dict = {}
        for user_id, accounts in self._users.items():
            raw[user_id] = {
                "accounts": [
                    {"email": acc.email, "passkey": acc.passkey} for acc in accounts
                ]
            }
        data = json.dumps(raw, ensure_ascii=False).encode()
        encrypted = self._fernet.encrypt(data)
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        self._store_path.write_bytes(encrypted)

    async def register_account(
        self, user_id: str, email: str, passkey: str
    ) -> None:
        """注册或更新用户邮箱账号。"""
        async with self._lock:
            accounts = self._users.setdefault(user_id, [])
            # 更新已有账号或新增
            for acc in accounts:
                if acc.email == email:
                    acc.passkey = passkey
                    break
            else:
                accounts.append(EmailAccount(email=email, passkey=passkey))
            await self._persist()
            logger.info("account_registered", user_id=user_id, email=email)

    async def remove_account(self, user_id: str, email: str) -> bool:
        """移除用户邮箱账号，返回是否成功移除。"""
        async with self._lock:
            accounts = self._users.get(user_id, [])
            for i, acc in enumerate(accounts):
                if acc.email == email:
                    accounts.pop(i)
                    if not accounts:
                        del self._users[user_id]
                    await self._persist()
                    logger.info("account_removed", user_id=user_id, email=email)
                    return True
            return False

    def get_account(self, user_id: str, email: str) -> Optional[EmailAccount]:
        """获取用户的指定邮箱账号信息。"""
        for acc in self._users.get(user_id, []):
            if acc.email == email:
                return acc
        return None

    def validate_access(self, user_id: str, email: str) -> EmailAccount:
        """校验用户对邮箱的访问权限，失败抛出异常。"""
        account = self.get_account(user_id, email)
        if not account:
            raise PermissionError(
                f"用户 {user_id} 未注册邮箱 {email}，请先通过 /api/v1/register 注册"
            )
        return account

    def list_accounts(self, user_id: str) -> list[str]:
        """列出用户已注册的所有邮箱地址。"""
        return [acc.email for acc in self._users.get(user_id, [])]


user_store = UserStore()