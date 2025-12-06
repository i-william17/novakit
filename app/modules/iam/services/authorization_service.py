from sqlalchemy.ext.asyncio import AsyncSession

class AuthorizationService:
    """
    Minimal authorization service to make the system work.
    Extend later to include full RBAC (roles, permissions, groups).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def user_can(self, user, permission: str) -> bool:
        """
        TEMPORARY IMPLEMENTATION:
        We assume the User model has a .permissions field
        (list of permission strings)
        """
        # Example: user.permissions is a list ["iamUsers", "iamDashboard"]
        if not hasattr(user, "permissions"):
            return False

        return permission in user.permissions
