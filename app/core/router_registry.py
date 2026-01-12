from fastapi import FastAPI

# Import all routers here
from app.modules.main.controllers.default_controller import  router as main_router
from app.modules.iam.controllers.http.user_controller import  router as iam_router
from app.modules.iam.controllers.http.auth_controller  import  router as iam_auth_router
from app.modules.main.controllers.setting_controller  import  router as main_setting_router





def register_routes(app: FastAPI):
    """Register all routers with prefixes and tags."""
    app.include_router(iam_auth_router, prefix="/v1/auth", tags=["IAM"])
    app.include_router(iam_router, prefix="/v1/iam", tags=["IAM"])
    app.include_router(main_router, prefix="/v1/main", tags=["Main"])
    app.include_router(main_setting_router, prefix="/v1/main", tags=["Settings"])



    # app.include_router(user_router, prefix="/api/v1/users", tags=["Users"])
