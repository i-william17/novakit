from typing import Annotated, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession

from config.config import settings
from app.common.db.sessions import get_db
from app.modules.iam.repositories.user_repository import UserRepository
from app.modules.iam.hooks.jwt_utils import decode_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")
user_repo = UserRepository()
# user_svc = UserService()


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)):
    """
    Decode token and load user. Raises 403 if invalid.
    Token format/secret must match what UserService.generate_jwt creates (uses same secret).
    """
    try:
        payload = user_svc.decode_jwt(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials")

    # jti is auth_key / unique JTI per user
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials")

    user = await user_repo.get_by_jti(db, jti)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # optionally check status
    if user.status != getattr(settings, "ACTIVE_STATUS", 10):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user


def require_permission(permission: str) -> Callable:
    """
    Dependency factory. Use like Depends(require_permission("iamUsers")).
    Checks if current user has permission. You must implement RBAC check in AuthorizationService.
    """
    from app.modules.iam.services.authorization_service import AuthorizationService  # you must implement this

    async def _checker(current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        authz = AuthorizationService(db)
        allowed = await authz.user_can(current_user, permission)
        if not allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return current_user

    return _checker


# for other modules to reuse
CurrentUser = get_current_user
