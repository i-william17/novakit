import uuid
from fastapi import Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.base_controller import BaseController, route
from app.common.router import create_module_router

from app.common.db.sessions import get_db
from app.core.security.brute_force import BruteForceService

from app.modules.iam.models.user import User
from app.modules.iam.models.refresh_tokens import RefreshToken

from app.modules.iam.schemas.auth import (
    LoginInput,
    ChangePasswordInput,
    PasswordResetRequestInput,
    ResetPasswordInput
)

from app.modules.iam.hooks.security import (
    generate_jwt_access_token,
    verify_password,
    hash_password
)

from app.modules.iam.repositories.user_repository import UserRepository
from app.modules.iam.services import user_service
from app.modules.iam.services.user_service import UserService


class AuthController(BaseController):

    def __init__(self):
        self.router = create_module_router("iam", tags=["IAM"])
        self.user_repo = UserRepository()
        self.user_service = UserService()
        self.register_routes()

    # ------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------
    def payload_response(self, data, meta=None, status_code=200):
        return JSONResponse(
            content={"dataPayload": data, **(meta or {})},
            status_code=status_code,
        )

    def error_response(self, errors, status_code=400):
        return JSONResponse(
            content={"errors": errors, "statusCode": status_code},
            status_code=status_code
        )

    def alertify_response(self, meta, status_code=200):
        return JSONResponse(content=meta, status_code=status_code)

    # ------------------------------------------------------
    # LOGIN
    # ------------------------------------------------------
    @route("post", "/login", summary="Login user")
    async def login(
            self,
            request: Request,
            response: Response,
            body: LoginInput,
            db: AsyncSession = Depends(get_db),
    ):

        client_ip = request.client.host
        username = body.email

        # -------------------------------------------
        # 1. Check if user/IP is blocked
        # -------------------------------------------
        block = await BruteForceService.is_blocked(username, client_ip)
        if block["user_blocked"] or block["ip_blocked"]:
            return self.error_response(
                errors="Too many failed login attempts. Try again later.",
                status_code=429
            )

        # Validate credentials via service
        user, errors = await  UserService.validate_credentials(
            db,
            body.email,
            body.password
        )

        if errors:
            return self.error_response(
                errors=errors,
                status_code=422
            )

        # Generate Access Token
        access_token = generate_jwt_access_token(user)

        # Generate Refresh Token (stored + HTTP Only cookie)
        await self.generate_refresh_token(user, request, response, db)

        # Response
        return self.payload_response(
            data={
                "access_token": access_token,
                "userData": user.myData,  # your custom property
            },
            meta={
                "statusCode": 200,
                "message": "Access granted",
                "type": "toast",
            },
        )

    # ------------------------------------------------------
    # REFRESH TOKEN
    # ------------------------------------------------------
    @route("post", "/refresh", summary="Refresh JWT")
    async def refresh(
        self,
        request: Request,
        response: Response,
        db: AsyncSession = Depends(get_db)
    ):
        masked = request.cookies.get("refresh_token")

        if not masked:
            return self.alertify_response({
                "statusCode": 401,
                "type": {"route": "/login"}
            }, status_code=401)

        refresh_token = masked

        token_model = await self.user_repo.get_refresh_token_by_token(db, refresh_token)

        if not token_model:
            return self.alertify_response({
                "statusCode": 401,
                "message": "Session has expired",
                "type": {"route": "iam/auth/login"}
            }, status_code=401)

        user = await self.user_repo.get_by_id(db, token_model.user_id)

        if not user:
            await self.user_repo.purge_refresh_tokens(db, token_model.user_id)
            await db.commit()

            return self.alertify_response({
                "statusCode": 401,
                "message": "Your account has been deactivated.",
                "type": {"route": "iam/auth/login"}
            }, status_code=401)

        # rotate refresh token
        await self.generate_refresh_token(user, request, response, db)
        new_access_token = generate_jwt_access_token(user)

        return self.payload_response({"access_token": new_access_token})

    # ------------------------------------------------------
    # LOGOUT
    # ------------------------------------------------------
    @route("post", "/logout", summary="Logout user")
    async def logout(
        self,
        request: Request,
        response: Response,
        db: AsyncSession = Depends(get_db),
    ):
        masked = request.cookies.get("refresh_token")

        if masked:
            refresh_token = masked
            token_model = await self.user_repo.get_refresh_token_by_token(db, refresh_token)

            if token_model:
                await self.user_repo.purge_refresh_tokens(db, token_model.user_id)
                await db.commit()

            response.delete_cookie("refresh_token")

        return self.alertify_response({
            "statusCode": 200,
            "type": {"route": "iam/auth/login"}
        })

    # ------------------------------------------------------
    # CHANGE PASSWORD
    # ------------------------------------------------------
    @route("post", "/change-password", summary="Change user password")
    async def change_password(
        self,
        body: ChangePasswordInput,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(UserService().require_login)
    ):
        error = await body.validate_business_rules(db, current_user)
        if error:
            return self.error_response(error)

        await self.user_service.change_password(db, current_user, body)

        return self.alertify_response({
            "statusCode": 200,
            "type": {
                "route": "iam/auth/login",
                "message": "Please login with your new password."
            }
        })

    # ------------------------------------------------------
    # REQUEST RESET PASSWORD
    # ------------------------------------------------------
    @route("post", "/request-password-reset")
    async def request_password_reset(
        self,
        body: PasswordResetRequestInput,
        db: AsyncSession = Depends(get_db)
    ):
        sent = await self.user_service.send_reset_email(body.email)

        if not sent:
            return self.error_response({"email": ["Could not send email"]})

        return self.alertify_response({
            "statusCode": 200,
            "type": {
                "route": "iam/auth/login",
                "message": "Password reset link has been sent to your email."
            }
        })

    # ------------------------------------------------------
    # RESET PASSWORD
    # ------------------------------------------------------
    @route("post", "/reset-password/{token}")
    async def reset_password(
        self,
        token: str,
        body: ResetPasswordInput,
        db: AsyncSession = Depends(get_db)
    ):
        user = await self.user_service.verify_reset_token(token)

        if not user:
            return JSONResponse({"detail": "Invalid token"}, status_code=400)

        user.password_hash = hash_password(body.password)
        await db.commit()

        return self.alertify_response({
            "statusCode": 200,
            "type": {
                "route": "iam/auth/login",
                "message": "Password has been reset successfully."
            }
        })

    # ------------------------------------------------------
    # GENERATE REFRESH TOKEN (Yii2 style)
    # ------------------------------------------------------
    async def generate_refresh_token(
        self,
        user: User,
        request: Request,
        response: Response,
        db: AsyncSession
    ):
        ua = request.headers.get("User-Agent", "unknown")
        ip = request.client.host

        existing = await self.user_repo.get_refresh_token(db, user.id)

        if not existing:
            refresh_token = uuid.uuid4().hex + uuid.uuid4().hex
            token_model = RefreshToken(
                user_id=user.id,
                token=refresh_token,
                user_agent=ua,
                ip=ip,
            )
            db.add(token_model)
        else:
            token_model = existing

        await db.commit()

        response.set_cookie(
            key="refresh_token",
            value=token_model.token,
            httponly=True,
            secure=False,
            samesite="lax",
            path="/v1/iam/auth"
        )

        return token_model


controller = AuthController()
router = controller.router


# fingerprint = Fingerprint.generate(
#     request.headers.get("user-agent"),
#     request.client.host
# )
#
# await RefreshTokenRepo.store(
#     user_id=user.id,
#     token=refresh_token,
#     fingerprint=fingerprint,
#     device_name=parse_device(request),
#     ip=request.client.host,
#     location=await GeoGuard.get_country(request.client.host)
# )


# if await IPReputation.is_bad(ip):
#     return self.error_response("Your IP is flagged for abuse", status_code=403)
