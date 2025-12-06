from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

class AssignmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def assign(self, user_id, permissions: List[str]) -> int:
        """
        Insert assignments into RBAC assignment table.
        Return number of inserted rows (int).
        """
        # TODO: implement actual DB insertion based on your rbac schema
        # Example pseudo:
        # for p in permissions: insert into auth_assignment (item_name, user_id, created_at)
        return len(permissions)

    async def revoke(self, user_id, permissions: List[str]) -> int:
        # TODO: implement
        return len(permissions)

    async def get_items(self, user_id):
        # return list of assigned items for the user
        return []
