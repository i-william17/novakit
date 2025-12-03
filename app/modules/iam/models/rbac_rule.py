from sqlalchemy import String, LargeBinary, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class RbacRule(Base):
    __tablename__ = "auth_rule"

    # Primary key (name)
    name: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
