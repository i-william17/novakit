import uuid
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
from passlib.context import CryptContext
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.iam.models.user import User
from app.modules.iam.models.password_history import PasswordHistory
from app.modules.iam.models.refresh_tokens import RefreshToken
from app.modules.iam.models.profile import Profile
from config.config import settings
from app.modules.iam.services.menu_service import MenuService

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -----------------------------------------------------------------------------
# Helpers that mirror your Yii2 secret + expiry logic
# -----------------------------------------------------------------------------
def _get_secret_key() -> str:
    return hashlib.sha256(
        (datetime.utcnow().strftime("%DYM") + settings.APP_ID).encode()
    ).hexdigest()


def _get_expire_timestamp() -> int:
    if getattr(settings, "APP_ENVIRONMENT", "prod") == "dev":
        return int((datetime.utcnow() + timedelta(minutes=180)).timestamp())
    return int((datetime.utcnow() + timedelta(minutes=30)).timestamp())


def _header_token() -> Dict[str, str]:
    return {"app": getattr(settings, "APP_NAME", settings.APP_ID)}


# =============================================================================
#                                 USER SERVICE
# =============================================================================
class UserService:
    ALGO = "HS256"

    # =========================
    # Basic DB lookups
    # =========================
    @staticmethod
    async def find_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        q = await db.execute(
            select(User).where(
                User.user_id == user_id,
                User.status == getattr(settings, "ACTIVE_STATUS", 10),
            )
        )
        return q.scalar_one_or_none()

    @staticmethod
    async def find_by_username(db: AsyncSession, username: str) -> Optional[User]:
        q = await db.execute(
            select(User).where(
                User.username == username,
                User.status == getattr(settings, "ACTIVE_STATUS", 10),
            )
        )
        return q.scalar_one_or_none()

    @staticmethod
    async def find_by_jti(db: AsyncSession, jti: str) -> Optional[User]:
        q = await db.execute(
            select(User).where(
                User.auth_key == jti,
                User.status == getattr(settings, "ACTIVE_STATUS", 10),
            )
        )
        return q.scalar_one_or_none()

    # =========================
    # Yii2 equivalents: getId()
    # =========================
    @staticmethod
    def get_id(user: User):
        """Equivalent to Yii2 getId()"""
        return user.user_id

    # =========================
    # Yii2 equivalents:
    # getAuthKey(), validateAuthKey()
    # =========================
    @staticmethod
    def get_auth_key(user: User) -> str:
        return user.auth_key

    @staticmethod
    def validate_auth_key(user: User, incoming_key: str) -> bool:
        return user.auth_key == incoming_key

    # =========================
    # Password helpers
    # =========================
    @staticmethod
    def hash_password(raw: str) -> str:
        return _pwd_ctx.hash(raw)

    @staticmethod
    async def set_password(db: AsyncSession, user: User, raw: str):
        """Yii2 setPassword() equivalent"""
        user.password_hash = UserService.hash_password(raw)
        await db.flush()

    @staticmethod
    def verify_password(raw: str, hashed: str) -> bool:
        return _pwd_ctx.verify(raw, hashed)

    # =========================
    # JWT + Auth Key
    # =========================
    @staticmethod
    def generate_auth_key() -> str:
        """Yii2 generateAuthKey()"""
        return uuid.uuid4().hex

    @staticmethod
    def generate_jwt(user: User, host: str = "") -> str:
        secret = _get_secret_key()
        now = int(time.time())
        payload = {
            "iss": host,
            "aud": host,
            "iat": now,
            "nbf": now,
            "exp": _get_expire_timestamp(),
            "jti": user.auth_key or UserService.generate_auth_key(),
        }
        return jwt.encode(
            payload,
            secret,
            algorithm=UserService.ALGO,
            headers=_header_token(),
        )

    @staticmethod
    def decode_jwt(token: str) -> dict:
        secret = _get_secret_key()
        try:
            return jwt.decode(token, secret, algorithms=[UserService.ALGO], options={"verify_aud": False})
        except jwt.PyJWTError as exc:
            raise ValueError("Invalid token") from exc

    # =========================
    # Password reset / email tokens
    # =========================
    @staticmethod
    def generate_password_reset_token() -> str:
        stamp = int(time.time())
        rand = uuid.uuid4().hex[:16]
        return f"{rand}_{stamp}"

    @staticmethod
    def generate_email_verification_token() -> str:
        stamp = int(time.time())
        rand = uuid.uuid4().hex[:16]
        return f"{rand}_{stamp}"

    @staticmethod
    def is_password_reset_token_valid(token: Optional[str], expire_seconds: int = 3600) -> bool:
        if not token:
            return False
        try:
            timestamp = int(token.rsplit("_", 1)[1])
            return timestamp + expire_seconds >= int(time.time())
        except Exception:
            return False

    # =========================
    # After save (purge tokens)
    # =========================
    @staticmethod
    async def after_save_purge_tokens(db: AsyncSession, user: User, changed: list):
        if "password_hash" in changed:
            await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.user_id))
            await db.commit()

    # =========================
    # Password history
    # =========================
    @staticmethod
    async def update_password_history(db: AsyncSession, user: User, raw_password: str):
        ph = PasswordHistory(
            user_id=user.user_id,
            old_password=hashlib.md5(raw_password.encode()).hexdigest(),
        )
        db.add(ph)
        await db.flush()
        return ph

    @staticmethod
    async def validate_password_history(db: AsyncSession, user: User, raw_password: str) -> bool:
        digest = hashlib.md5(raw_password.encode()).hexdigest()
        q = await db.execute(
            select(PasswordHistory).where(
                PasswordHistory.user_id == user.user_id,
                PasswordHistory.old_password == digest,
            )
        )
        return q.scalars().first() is None

    # =========================
    # Relations: profile + refresh tokens
    # =========================
    @staticmethod
    async def get_profile(db: AsyncSession, user: User) -> Optional[Profile]:
        """Equivalent of Yii2 getProfile()"""
        q = await db.execute(select(Profile).where(Profile.id == user.profile_id))
        return q.scalar_one_or_none()

    @staticmethod
    async def get_refresh_tokens(db: AsyncSession, user: User):
        """Equivalent of Yii2 getRefreshTokens()"""
        q = await db.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.user_id)
        )
        return q.scalars().all()

    # =========================
    # Access control (menus + permissions)
    # =========================
    @staticmethod
    async def access_control(db: AsyncSession, user: User) -> dict:
        permissions = []  # TODO: plug in RBAC tables
        menus = {}
        try:
            menu_svc = MenuService()
            menus = await menu_svc.load_all_menus(user, permissions=permissions)
        except Exception:
            pass
        return {"menus": menus, "permissions": permissions}

    # =========================
    # Register new user
    # =========================
    @staticmethod
    async def create_user(
        db: AsyncSession, username: str, password: str, profile_id: Optional[str] = None
    ) -> User:
        user = User(
            user_id=uuid.uuid4(),
            username=username,
            profile_id=profile_id,
            auth_key=UserService.generate_auth_key(),
            password_hash=UserService.hash_password(password),
            status=getattr(settings, "DEFAULT_USER_STATUS", 10),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
