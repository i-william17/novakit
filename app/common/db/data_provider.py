from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

class DataProvider:
    def __init__(
        self,
        query,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        sort: Optional[str] = None,
        default_sort: Optional[str] = None,
    ):
        self.query = query
        self.db = db
        self.page = max(page, 1)
        self.page_size = min(max(page_size, 1), 100)
        self.sort = sort
        self.default_sort = default_sort

    async def get_page(self):
        # Apply sorting
        if self.sort:
            if self.sort.startswith("-"):
                self.query = self.query.order_by(getattr(self.model, self.sort[1:]).desc())
            else:
                self.query = self.query.order_by(getattr(self.model, self.sort).asc())
        elif self.default_sort:
            field = self.default_sort.lstrip("-")
            if self.default_sort.startswith("-"):
                self.query = self.query.order_by(getattr(self.model, field).desc())
            else:
                self.query = self.query.order_by(getattr(self.model, field).asc())

        # Count total
        count_q = select(func.count()).select_from(self.query.subquery())
        total = (await self.db.execute(count_q)).scalar()

        # Fetch results
        offset = (self.page - 1) * self.page_size
        rows = (await self.db.execute(self.query.limit(self.page_size).offset(offset))).scalars().all()

        return {
            "items": rows,
            "page": self.page,
            "page_size": self.page_size,
            "total": total,
            "pages": (total // self.page_size) + (1 if total % self.page_size else 0),
        }
