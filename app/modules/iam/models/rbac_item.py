from sqlalchemy import String, SmallInteger, Text, LargeBinary, Integer, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class RbacItem(Base):
    __tablename__ = "auth_item"

    name: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    type: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_name: Mapped[str | None] = mapped_column(String(64), ForeignKey("auth_rule.name", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # optional relationship to rule (useful)
    rule = relationship("RbacRule", backref="items", lazy="joined")

    __table_args__ = (
        Index("idx_auth_item_type", "type"),
    )
