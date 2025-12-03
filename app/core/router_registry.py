from fastapi import FastAPI

# Import all routers here
from app.modules.main.controllers.default_controller import  router as main_router
# from app.modules.users.endpoints.UserEndpoint import router as user_router
 


def register_routes(app: FastAPI):
    """Register all routers with prefixes and tags."""
    app.include_router(main_router, prefix="/api/v1/main", tags=["Main"])
    # app.include_router(user_router, prefix="/api/v1/users", tags=["Users"])
