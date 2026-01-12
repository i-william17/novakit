from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.modules.iam.hooks.base_model import IamBaseModel

class Profile(IamBaseModel):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    email_address: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    data: Mapped[dict | None] = mapped_column(JSON)
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(Integer, default=10)

    # 1:1 relationship back → ONLY STRING
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
        uselist=False
    )
