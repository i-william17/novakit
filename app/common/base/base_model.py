import time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer


class Base(DeclarativeBase):
    pass


class BaseModel(Base):
    __abstract__ = True

    created_at: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=lambda: int(time.time()),
    )

    updated_at: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=lambda: int(time.time()),
        onupdate=lambda: int(time.time()),
    )
