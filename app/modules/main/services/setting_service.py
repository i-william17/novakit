from typing import List

from app.common.base.base_service import BaseService
from app.modules.main.repositories.settings_repository import SettingsRepository
from app.modules.main.schemas.settings.base import BaseSettingGroup
from app.modules.main.schemas.system_setting_schema import SystemSettingResponse

class SettingService(BaseService):
    repo = SettingsRepository

    async def ensure_settings(self, definition_cls: type[BaseSettingGroup]):
        """
        Checks if settings for this definition group exist.
        If not, it seeds them into the database using the defaults.
        """
        definitions = definition_cls.get_definitions()
        if not definitions:
            return

        expected_keys = [d.key for d in definitions]
        existing_keys = await self.repository.get_existing_keys(expected_keys)
        existing_set = set(existing_keys)

        new_entries = []
        for d in definitions:
            if d.key not in existing_set:
                new_entries.append({
                    "key": d.key,
                    "label": d.label,
                    "category": definition_cls.CATEGORY,
                    "default_value": str(d.default_value),
                    "current_value": None,
                    "disposition": d.disposition,
                    "input_type": d.input_type,
                    "input_preload": str(d.input_preload) if d.input_preload else None
                })

        if new_entries:
            for entry in new_entries:

                instance = self.repository.model(**entry)
                await self.repository.add(instance)


            await self.commit()
    #
    # async def get_formatted_settings(self, category: str) -> List[SystemSettingResponse]:
    #     """
    #     Returns settings in a format ready for the frontend form.
    #     """
    #
    #     settings = await self.repository.list_active(filters={"category": category})
    #
    #
    #
    #     # return settings
    #     return [SystemSettingResponse.model_validate(s) for s in settings]
    async def get_formatted_settings(self, category: str) -> dict:
        """
        Returns settings as a simple Key-Value dictionary.
        Example: {"smtp_server": "mail.example.com", "smtp_port": "587"}
        """

        # 1. Get the raw settings from DB
        settings_list = await self.repository.list_active(filters={"category": category})

        # 2. Transform into a simple dictionary
        simple_settings = {}

        for setting in settings_list:
            # Logic: Use the current_value if the user set one, otherwise use default_value
            final_value = setting.current_value if setting.current_value is not None else setting.default_value

            # Map the key to the value
            simple_settings[setting.key] = final_value

        return simple_settings

    async def update_setting_value(self, key: str, value: str):
        """
        Updates a single setting value.
        """
        setting = await self.repository.get_by_key(key)
        if setting:

            await self.repository.update(setting, {"current_value": str(value)})
            await self.commit()
            return setting
        return None