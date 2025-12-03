import uuid
from sqlalchemy import String, Integer, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.modules.iam.hooks.base_model import IamBaseModel

class RefreshToken(IamBaseModel):
    __tablename__ = "refresh_tokens"

    id = None

    token_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True
    )

    token: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    ip: Mapped[str] = mapped_column(String(32), server_default="127.0.0.1")
    user_agent: Mapped[str] = mapped_column(String, nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")
