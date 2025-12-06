import uuid
from typing import List

from fastapi import Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.base_controller import BaseController, route
from app.common.router import create_module_router

from app.modules.iam.schemas.user import (
    UserOut,
    UserCreate,
    UserBase,
)
from app.modules.iam.repositories.user_repository import UserRepository
from app.modules.iam.services.user_service import UserService
from app.modules.iam.models.searches.user_search import UserSearch
from app.common.db.sessions import get_db
from app.modules.iam.hooks.auth import require_permission


class AssignRequest(BaseModel):
    permissions: List[str]


class UserController(BaseController):
    """IAM User Management API (FastAPI Modular Style)"""

    def __init__(self):
        # same style as DefaultController
        self.router = create_module_router("iam", tags=["IAM"])
        self.user_repo = UserRepository()
        self.user_service = UserService()
        self.register_routes()

    # ---------------------------------------------------------
    # LIST USERS
    # ---------------------------------------------------------
    @route("get", "/", summary="List/search users")
    async def index(
        self,
        q: UserSearch = Depends(),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(require_permission("iamUsers")),
    ):
        page = await q.search(db)
        return JSONResponse(
            content={"data": page, "oneRecord": False},
            status_code=status.HTTP_200_OK,
        )

    # ---------------------------------------------------------
    # VIEW USER
    # ---------------------------------------------------------
    @route("get", "/{identifier}", summary="Get user (UUID or username)", response_model=UserOut)
    async def view(
        self,
        identifier: str,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(require_permission("iamUsers")),
    ):
        found = None

        # try UUID first
        try:
            uid = uuid.UUID(identifier)
            found = await self.user_repo.get_by_id(db, uid)
        except Exception:
            # fallback to username
            found = await self.user_repo.get_by_username(db, identifier)

        if not found:
            return JSONResponse(
                content={"message": "The requested user does not exist."},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return UserOut.from_orm(found)

    # ---------------------------------------------------------
    # ASSIGN PERMISSIONS
    # ---------------------------------------------------------
    @route("post", "/{uid}/assign", summary="Assign permissions")
    async def assign_permissions(
        self,
        uid: uuid.UUID,
        body: AssignRequest,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(require_permission("iamUsers")),
    ):
        # TODO: Connect service logic later
        return JSONResponse(
            content={
                "statusCode": 202,
                "message": "Assignment functionality not implemented yet",
                "permissions": body.permissions,
            },
            status_code=status.HTTP_202_ACCEPTED,
        )

    # ---------------------------------------------------------
    # REVOKE PERMISSIONS
    # ---------------------------------------------------------
    @route("post", "/{uid}/revoke", summary="Revoke permissions")
    async def revoke_permissions(
        self,
        uid: uuid.UUID,
        body: AssignRequest,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(require_permission("iamUsers")),
    ):
        # TODO: Connect service logic later
        return JSONResponse(
            content={
                "statusCode": 202,
                "message": "Revoke functionality not implemented yet",
                "permissions": body.permissions,
            },
            status_code=status.HTTP_202_ACCEPTED,
        )


# Export instance (important for auto loader)
controller = UserController()
router = controller.router
