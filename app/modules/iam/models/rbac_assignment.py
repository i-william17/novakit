# rbac_assignment.py
from sqlalchemy import String, Integer, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class RbacAssignment(Base):
    __tablename__ = "auth_assignment"

    item_name: Mapped[str] = mapped_column(String(64), ForeignKey("auth_item.name", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint("item_name", "user_id", name="pk_auth_assignment"),
    )
