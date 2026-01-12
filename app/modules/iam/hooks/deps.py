from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from config.config import settings
from app.common.db.sessions import AsyncSessionLocal, get_db  # your existing get_db
from app.modules.iam.services import UserService
from app.modules.iam.models import User
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login/access-token")

async def get_session() -> AsyncSession:
    # your global get_db() already yields a session
    async for s in get_db():
        yield s

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: AsyncSession = Depends(get_session)) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"], audience=settings.APP_ID if getattr(settings, "APP_ID", None) else None, options={"verify_aud": False})
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid auth token")
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="Token missing jti")
    # find user by auth_key (jti)
    svc = UserService(session)
    # simple query
    stmt_user = await svc.get_by_username_or_404  # not used; we will search by auth_key
    # Query by auth_key
    from sqlalchemy import select
    from .models import User
    r = await session.execute(select(User).where(User.auth_key == jti, User.is_deleted == 0))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_permission(permission_name: str):
    async def _checker(current_user: User = Depends(get_current_user)):
        # Here you should call your RBAC/authManager layer to check if user has permission
        # Placeholder uses a simple attribute check (replace with real check)
        # Example: if not auth_manager.check_permission(current_user.user_id, permission_name): raise HTTPException(403)
        # For now we'll just allow if user.status == 10 (active) — replace this with real logic.
        if current_user.status != 10:
            raise HTTPException(status_code=403, detail="Forbidden")
        # TODO: integrate with your RBAC (authManager.getPermissionsByUser)
        return True
    return _checker

#
# from fastapi import Depends
# from app.core.nova.py import nova.py
# from app.modules.iam.security.auth import decode_token
#
#
# async def get_current_user(token: str = Depends(oauth2_scheme)):
#     user = await decode_token(token)
#     nova.py.user.set(user)     # <--- THE MAGIC
#     return user
