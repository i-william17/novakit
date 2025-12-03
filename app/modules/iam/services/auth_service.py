from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from novakit.app.modules.iam.models import User
from .utils import hash_password, verify_password, generate_auth_key, generate_token_jwt

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, username: str, profile_id: str, password: str) -> User:
        # ensure unique username/profile_id; simple check
        stmt = select(User).where(User.username == username)
        r = await self.session.execute(stmt)
        if r.scalar_one_or_none():
            raise HTTPException(400, "username already exists")

        stmt2 = select(User).where(User.profile_id == profile_id)
        r2 = await self.session.execute(stmt2)
        if r2.scalar_one_or_none():
            raise HTTPException(400, "profile_id already registered")

        user = User(
            username=username,
            profile_id=profile_id,
            password_hash=hash_password(password),
            auth_key=generate_auth_key(),
            status=10,
            is_deleted=0,
            created_at=int(__import__("time").time()),
            updated_at=int(__import__("time").time()),
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def authenticate(self, username: str, password: str):
        stmt = select(User).where(User.username == username, User.is_deleted == 0)
        r = await self.session.execute(stmt)
        user = r.scalar_one_or_none()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def get_by_username_or_404(self, username: str) -> User:
        stmt = select(User).where(User.username == username)
        r = await self.session.execute(stmt)
        user = r.scalar_one_or_none()
        if not user:
            raise HTTPException(404, "User not found")
        return user

    async def list(self, filters: dict | None = None):
        stmt = select(User)
        if filters:
            stmt = stmt.filter_by(**filters)
        r = await self.session.execute(stmt)
        return r.scalars().all()

    async def generate_jwt_for_user(self, user: User):
        # returns token using user's auth_key as jti (close to your Yii logic)
        return generate_token_jwt(jti=user.auth_key)

    # -----------------------
    # RBAC assign/revoke placeholders
    # -----------------------
    async def assign_permissions(self, user_id: int, permissions: list[str]) -> int:
        """
        Assign permissions/roles to a user.
        This is a placeholder; wire to your authManager or DB tables.
        Return number of assigned items.
        """
        # TODO: integrate with your RBAC store (auth_rule/assignment tables)
        # For now return len(permissions) to indicate "success"
        return len(permissions)

    async def revoke_permissions(self, user_id: int, permissions: list[str]) -> int:
        """
        Revoke permissions/roles from a user.
        Placeholder.
        """
        return len(permissions)
