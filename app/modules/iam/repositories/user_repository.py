import uuid
from sqlalchemy import or_
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.iam.models.user import User
from app.modules.iam.hooks.user_status import UserStatus
from app.modules.iam.models.password_history import PasswordHistory
from app.modules.iam.models.refresh_tokens import RefreshToken
from app.modules.iam.models.profile import Profile
from config.config import settings

# noinspection PyMethodMayBeStatic
class UserRepository:

    async def get_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        q = await db.execute(
            select(User).where(
                User.user_id == user_id,
                User.status == UserStatus.ACTIVE,
            )
        )
        return q.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        q = await db.execute(
            select(User).where(
                User.username == username,
                User.status == UserStatus.ACTIVE,
            )
        )
        return q.scalar_one_or_none()

    async def get_by_username_or_email(
            self,
            db: AsyncSession,
            identifier: str,
    ) -> Optional[User]:
        q = await db.execute(
            select(User)
            .join(Profile)
            .where(
                User.status == UserStatus.ACTIVE,
                or_(
                    User.username == identifier,
                    Profile.email_address == identifier,
                ),
            )
        )
        return q.scalar_one_or_none()

    async def get_by_jti(self, db: AsyncSession, jti: str) -> Optional[User]:
        q = await db.execute(
            select(User).where(
                User.auth_key == jti,
                User.status == UserStatus.ACTIVE,
            )
        )
        return q.scalar_one_or_none()

    # ──────────── Profile ─────────────

    async def get_profile(self, db: AsyncSession, user: User) -> Optional[Profile]:
        q = await db.execute(select(Profile).where(Profile.id == user.profile_id))
        return q.scalar_one_or_none()

    # ──────────── Refresh Tokens ─────────────

    async def get_refresh_token(self, db: AsyncSession, user: User):
        result = await db.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == user.user_id)
            .limit(1)
        )
        return result.scalars().first()

    async def purge_refresh_tokens(self, db: AsyncSession, user_id: uuid.UUID):
        await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))

    # Refresh tokens
    async def get_refresh_token_by_token(self, db: AsyncSession, token: str):
        q = await db.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        return q.scalar_one_or_none()

    # ──────────── Password History ─────────────

    async def add_password_history(self, db: AsyncSession, ph: PasswordHistory):
        db.add(ph)
        await db.flush()

    async def find_password_in_history(self, db: AsyncSession, user: User, digest: str):
        q = await db.execute(
            select(PasswordHistory).where(
                PasswordHistory.user_id == user.user_id,
                PasswordHistory.old_password == digest,
            )
        )
        return q.scalar_one_or_none()

    async def username_exists(self, db: AsyncSession, username: str) -> bool:
        q = await db.execute(
            select(User.user_id).where(User.username == username)
        )
        return q.scalar_one_or_none() is not None

    async def email_exists(self, db: AsyncSession, email: str) -> bool:
        q = await db.execute(
            select(Profile.id).where(Profile.email_address == email)
        )
        return q.scalar_one_or_none() is not None

    async def phone_exists(self, db: AsyncSession, phone: str) -> bool:
        q = await db.execute(
            select(Profile.id).where(Profile.phone_number == phone)
        )
        return q.scalar_one_or_none() is not None
