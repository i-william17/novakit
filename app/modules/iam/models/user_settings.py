import uuid
from sqlalchemy import Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.modules.iam.hooks.base_model import IamBaseModel

class UserSettings(IamBaseModel):
    __tablename__ = "user_settings"

    id = None

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        unique=True,
        nullable=False
    )

    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[int] = mapped_column(Integer, server_default="10", nullable=False)

    user = relationship("User", back_populates="settings")
