from sqlalchemy import String, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class RbacItemChild(Base):
    __tablename__ = "auth_item_child"

    parent: Mapped[str] = mapped_column(String(64), ForeignKey("auth_item.name", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    child: Mapped[str] = mapped_column(String(64), ForeignKey("auth_item.name", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("parent", "child", name="pk_auth_item_child"),
    )
