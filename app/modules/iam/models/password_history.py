import uuid
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.modules.iam.hooks.base_model import IamBaseModel

class PasswordHistory(IamBaseModel):
    __tablename__ = "password_history"

    id = None

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )

    old_password: Mapped[str] = mapped_column(String, nullable=False)

    user = relationship("User", back_populates="password_history")
