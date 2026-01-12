from pydantic import BaseModel, ConfigDict
from typing import Optional

class SystemSettingResponse(BaseModel):
    # These match your SQLAlchemy model fields
    key: str
    label: str
    category: str
    disposition: int
    input_type: str
    current_value: Optional[str] = None
    default_value: str
    input_preload: Optional[str] = None

    # This magic config tells Pydantic: "It's okay to read data from a Class Object"
    model_config = ConfigDict(from_attributes=True)