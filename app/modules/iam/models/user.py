import uuid
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.modules.iam.hooks.base_model import IamBaseModel
from app.modules.iam.models.user_settings import UserSettings
from app.modules.iam.models.password_history import PasswordHistory
from app.modules.iam.models.refresh_tokens import RefreshToken

class User(IamBaseModel):
    __tablename__ = "users"

    id: None
    __mapper_args__ = {
        "exclude_properties": ["id"],
        "primary_key": ["user_id"],
    }

    user_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, unique=True
    )

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    # REQUIRED 1:1 FK → User must always have a profile
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    auth_key: Mapped[str | None] = mapped_column(String(64))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    password_reset_token: Mapped[str | None] = mapped_column(String(255))
    verification_token: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[int] = mapped_column(Integer, server_default="10", nullable=False)

    profile: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        single_parent=True,
        cascade="all, delete-orphan"
    )

    settings = relationship(
        UserSettings,
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    password_history = relationship(
        PasswordHistory,
        back_populates="user",
        cascade="all, delete-orphan"
    )

    refresh_tokens = relationship(
        RefreshToken,
        back_populates="user",
        cascade="all, delete-orphan"
    )


    # otps = relationship(
    #     "app.modules.iam.models.otp.OneTimePassword",
    #     back_populates="user",
    #     cascade="all, delete-orphan"
    # )



    # class User(IamBaseModel):
    #     __tablename__ = "users"
    #
    #     id = None
    #
    #     user_id: Mapped[uuid.UUID] = mapped_column(
    #         primary_key=True,
    #         default=uuid.uuid4,
    #         unique=True
    #     )
    #

    # 2FA SETTINGS
    # otp_secret: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # otp_enabled: Mapped[bool] = mapped_column(Boolean, server_default="0", nullable=False)



    #     username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    #     profile_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    #
    #     auth_key: Mapped[str | None] = mapped_column(String(64))
    #     password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    #     password_reset_token: Mapped[str | None] = mapped_column(String(255))
    #     verification_token: Mapped[str | None] = mapped_column(String(255))
    #
    #     status: Mapped[int] = mapped_column(Integer, server_default="10", nullable=False)