from .base import BaseSettingGroup, SettingMetadata

class WhatsAppSettings(BaseSettingGroup):
    CATEGORY = "WHATSAPP"

    @classmethod
    def get_definitions(cls):
        return [
            SettingMetadata(key="wa_api_key", label="API Key", default_value=""),
        ]