from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db.sessions import get_db
from app.modules.iam.repositories.user_repository import UserRepository
from app.modules.iam.hooks.jwt_utils import decode_jwt

repo = UserRepository()


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    auth = request.headers.get("Authorization")

    if not auth:
        raise HTTPException(status_code=401, detail="Authentication required")

    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    try:
        payload = decode_jwt(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await repo.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")

    return user
