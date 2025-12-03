from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    repo = None   # Child MUST override: repo = UserRepository

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = self.repo(session)

    # -----------------------------------------------------
    # Commit helper
    # -----------------------------------------------------
    async def commit(self):
        try:
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            raise HTTPException(400, detail=str(e))

    # -----------------------------------------------------
    # CRUD USING REPOSITORY
    # -----------------------------------------------------
    async def create(self, data: dict):
        instance = self.repository.model(**data)
        await self.repository.add(instance)
        await self.commit()
        return instance

    async def update(self, id, data: dict):
        instance = await self.repository.get(id)
        if not instance:
            raise HTTPException(404, f"{self.repository.model.__name__} not found")

        await self.repository.update(instance, data)
        await self.commit()
        return instance

    async def delete(self, id):
        instance = await self.repository.get(id)
        if not instance:
            raise HTTPException(404, f"{self.repository.model.__name__} not found")

        await self.repository.delete(instance)
        await self.commit()
        return True

    async def remove(self, id):
        """
        Soft delete (Yii2 -> trash)
        """
        instance = await self.repository.get(id)
        if not instance:
            raise HTTPException(404, f"{self.repository.model.__name__} not found")

        # Soft delete
        if hasattr(instance, "is_deleted"):
            instance.is_deleted = True
            await self.commit()
            return instance

        # Hard delete
        await self.repository.delete(instance)
        await self.commit()
        return True

    # -----------------------------------------------------
    # READ / FIND
    # -----------------------------------------------------
    async def get(self, id):
        return await self.repository.get(id)

    async def get_or_404(self, id):
        obj = await self.repository.get(id)
        if not obj:
            raise HTTPException(404, f"{self.repository.model.__name__} not found")
        return obj

    async def find_model(self, id):
        return await self.get_or_404(id)

    async def list(self, filters: dict | None = None):
        return await self.repository.list(filters)

    async def list_active(self, filters: dict | None = None):
        return await self.repository.list_active(filters)
