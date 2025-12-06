from sqlalchemy.orm import Mapped, mapped_column
from app.modules.iam.hooks.base_model import IamBaseModel

class Profile(IamBaseModel):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int]
    first_name: Mapped[str] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=True)
