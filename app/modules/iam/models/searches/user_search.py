from sqlalchemy import select, or_
from typing import Optional
from pydantic import BaseModel

from app.common.db.data_provider import DataProvider
from app.common.db.filtering import or_filter_ilike
from app.modules.iam.models.user import User


class UserSearch(BaseModel):
    username: Optional[str] = None
    auth_key: Optional[str] = None
    q: Optional[str] = None
    status: Optional[int] = None

    page: int = 1
    page_size: int = 20
    sort: Optional[str] = None

    async def search(self, db):
        query = select(User)

        if self.username:
            query = or_filter_ilike(query, User, "username", self.username)

        if self.auth_key:
            query = or_filter_ilike(query, User, "auth_key", self.auth_key)

        if self.q:
            query = query.where(
                or_(
                    User.username.ilike(f"%{self.q}%"),
                    User.auth_key.ilike(f"%{self.q}%"),
                )
            )

        if self.status is not None:
            query = query.where(User.status == self.status)

        dp = DataProvider(
            query=query,
            db=db,
            page=self.page,
            page_size=self.page_size,
            sort=self.sort,
            default_sort="-created_at"
        )

        dp.model = User
        return await dp.get_page()
