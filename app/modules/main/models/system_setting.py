from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
# from app.modules.main.hooks.base_model import
from app.common.base.base_model import BaseModel

class SystemSetting(BaseModel):
    __tablename__ = "system_settings1"


    id = None

    key: Mapped[str] = mapped_column(String(128), primary_key=True, unique=True, nullable=False)

    label: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="GENERAL", nullable=False)
    disposition: Mapped[int] = mapped_column(Integer, nullable=False)
    input_type: Mapped[str] = mapped_column(String(64), nullable=False)

    current_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_value: Mapped[str] = mapped_column(Text, nullable=False)


    input_preload: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    def __repr__(self):
        return f"<SystemSetting(key='{self.key}')>"