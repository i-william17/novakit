from typing import Any, List, Optional
from pydantic import BaseModel,ConfigDict



class SettingMetadata(BaseModel):
    key: str
    label: str
    default_value: Any
    input_type: str = "textInput"
    input_preload: Optional[dict] = None
    disposition: int = 0


class SystemSettingResponse(SettingMetadata):
    # Inherits all fields from Metadata, adds the dynamic one
    current_value: Optional[str] = None

    # Allows Pydantic to read directly from your SQLAlchemy model
    model_config = ConfigDict(from_attributes=True)
class BaseSettingGroup:
    CATEGORY: str = "GENERAL"

    @classmethod
    def get_definitions(cls) -> List[SettingMetadata]:
        """
        Subclasses must implement this to return their specific settings.
        This replaces your old 'loadDefaultValues' logic.
        """
        raise NotImplementedError("Subclasses must implement get_definitions")