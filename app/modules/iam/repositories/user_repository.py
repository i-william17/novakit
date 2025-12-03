from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from novakit.app.modules.iam.models.users import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int):
        stmt = select(User).where(User.user_id == user_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_username(self, username: str):
        stmt = select(User).where(User.username == username)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list(self, filters: dict | None = None):
        stmt = select(User)
        if filters:
            stmt = stmt.filter_by(**filters)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def add(self, instance: User):
        self.session.add(instance)
        return instance

    async def delete(self, instance: User):
        await self.session.delete(instance)
        return True
