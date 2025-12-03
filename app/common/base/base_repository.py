from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class BaseRepository:
    model = None  # must be overridden by subclass

    def __init__(self, session: AsyncSession):
        self.session = session

    # -------------------------
    # BASIC FETCH METHODS
    # -------------------------

    async def get(self, id):
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active(self, id):
        """Soft delete aware"""
        stmt = select(self.model).where(
            self.model.id == id,
            getattr(self.model, "is_deleted", False) == False
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, filters=None):
        stmt = select(self.model)
        if filters:
            stmt = stmt.filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_active(self, filters=None):
        stmt = select(self.model).where(self.model.is_deleted == False)
        if filters:
            stmt = stmt.filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # -------------------------
    # WRITING (no commit)
    # -------------------------

    async def add(self, instance):
        self.session.add(instance)
        return instance

    async def delete(self, instance):
        await self.session.delete(instance)
        return True

    async def update(self, instance, data: dict):
        for key, value in data.items():
            setattr(instance, key, value)
        return instance
