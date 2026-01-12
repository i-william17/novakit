from .base import BaseSettingGroup, SettingMetadata

class GeneralSettings(BaseSettingGroup):
    CATEGORY = "General"

    @classmethod
    def get_definitions(cls):
        return [

            SettingMetadata(
                key="company_name",
                label="Company Name",
                default_value="kardiverse",
                disposition=1
            ),
        ]