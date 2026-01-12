from sqlalchemy import select
from app.common.base.base_repository import BaseRepository
from app.modules.main.models.system_setting import SystemSetting

class SettingsRepository(BaseRepository):

    model = SystemSetting

    async def get_by_key(self, key: str) -> SystemSetting | None:
        """
        Find a setting by its unique string key (e.g., 'smtp_port').
        """
        stmt = select(self.model).where(
            self.model.key == key,
            self.model.is_deleted == False
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_existing_keys(self, keys: list[str]) -> list[str]:
        """
        Optimized check to see which keys already exist in the DB.
        """
        stmt = select(self.model.key).where(
            self.model.key.in_(keys)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())