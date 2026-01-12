from typing import List, Literal
from pydantic import BaseModel, Field, EmailStr
from .base import BaseSettingGroup, SettingMetadata

class EmailSettingsSchema(BaseModel):
    smtp_server: str = Field(..., min_length=1, description="SMTP Server Hostname")
    smtp_port: int = Field(..., ge=1, le=65535, description="SMTP Port")
    smtp_username: str = Field(..., description="SMTP Username")
    smtp_password: str = Field(..., description="SMTP Password")
    email_encryption: Literal["ssl", "tls", "none"] = Field(..., description="Encryption Type")




class EmailSettingDefinition(BaseSettingGroup):
    CATEGORY = "EMAIL"
    VALIDATOR_SCHEMA = EmailSettingsSchema
    @classmethod
    def get_definitions(cls) -> List[SettingMetadata]:
        return [
            SettingMetadata(
                key="smtp_server",
                label="SMTP Server",
                default_value="mail.example.com",
                disposition=1
            ),
            SettingMetadata(
                key="smtp_port",
                label="Port",
                default_value="587",
                disposition=2,
                input_type="number"
            ),
            SettingMetadata(
                key="smtp_username",
                label="SMTP Username",
                default_value="noreply@example.com",
                disposition=3
            ),
            SettingMetadata(
                key="smtp_password",
                label="Password",
                default_value="emailpassword",
                disposition=4,
                input_type="passwordInput"
            ),
            SettingMetadata(
                key="email_encryption",
                label="Encryption",
                default_value="ssl",
                disposition=5,
                input_type="dropDownList",

                input_preload={"ssl": "SSL", "tls": "TLS", "none": "None"}
            ),
        ]
