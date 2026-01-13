"""
Enhanced auth middleware for microservices architecture
Integrates with the global AuthMiddleware
"""
import hashlib
from typing import Callable, Set, Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import httpx
import os
from functools import lru_cache

from config.config import settings
from .auth_middleware import AuthMiddleware as BaseAuthMiddleware

logger = logging.getLogger("shared.auth")


class MicroserviceAuthMiddleware(BaseAuthMiddleware):
    """
    Enhanced auth middleware for microservices

    Features:
    1. Token validation (local or via auth service)
    2. Service-to-service authentication
    3. Permission checking
    4. Multi-tenant support
    """

    def __init__(
            self,
            app: ASGIApp,
            safe_endpoints: Optional[Set[str]] = None,
            secret_key: Optional[str] = None,
            algorithm: str = "HS256",
            allow_cookie_refresh: bool = True,
            validate_with_auth_service: bool = False,
            auth_service_url: Optional[str] = None
    ):
        # Call parent init with your existing logic
        super().__init__(
            app=app,
            safe_endpoints=safe_endpoints,
            secret_key=secret_key,
            algorithm=algorithm,
            allow_cookie_refresh=allow_cookie_refresh
        )

        # Microservices-specific settings
        self.validate_with_auth_service = validate_with_auth_service
        self.auth_service_url = auth_service_url or os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
        self.service_secret = os.getenv("SERVICE_SECRET", "")

    async def _validate_token_with_service(self, token: str) -> Dict[str, Any]:
        """Validate token by calling auth service"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.auth_service_url}/auth/validate",
                    json={"token": token},
                    headers={
                        "Content-Type": "application/json",
                        "X-Service-Token": self.service_secret
                    }
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Auth service error: {response.text}"
                    )
        except httpx.RequestError as e:
            logger.error(f"Auth service unavailable: {e}")
            # Fall back to local validation
            return super()._validate_token(token)

    async def _validate_service_token(self, token: str) -> Dict[str, Any]:
        """Validate service-to-service token"""
        if token != self.service_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service token"
            )

        return {
            "service": os.getenv("SERVICE_NAME", "unknown"),
            "authenticated": True,
            "permissions": ["service_access"]
        }

    def _extract_token(self, request: Request) -> Optional[str]:
        """Extend token extraction for service tokens"""
        # First try parent method
        token = super()._extract_token(request)
        if token:
            return token

        # Try service token header
        service_token = request.headers.get("X-Service-Token")
        if service_token:
            return service_token

        return None

    async def dispatch(self, request: Request, call_next: Callable):
        """Enhanced dispatch with service token support"""
        path = request.url.path

        # Skip auth for safe endpoints
        if path in {"/", "/favicon.ico"}:
            return await call_next(request)

        if self._is_safe_endpoint(path):
            return await call_next(request)

        token = self._extract_token(request)
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"}
            )

        try:
            # Check if it's a service token
            is_service_token = request.headers.get("X-Service-Token") is not None

            if is_service_token:
                payload = await self._validate_service_token(token)
                auth_type = "service"
            else:
                # User token validation
                if self.validate_with_auth_service:
                    payload = await self._validate_token_with_service(token)
                else:
                    payload = super()._validate_token(token)
                auth_type = "user"

            # Attach enhanced auth context
            request.state.auth = {
                "payload": payload,
                "type": auth_type,
                "token": token,
                "authenticated": True,
                "ip": request.client.host if request.client else None,
                "ua": request.headers.get("User-Agent"),
            }

            # Backward compatibility
            if auth_type == "user":
                request.state.user = payload

            return await call_next(request)

        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )


# ---------------------------------------------------------
# FastAPI Dependencies for Auth
# ---------------------------------------------------------
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        validate_with_service: bool = False
) -> Dict[str, Any]:
    """FastAPI dependency to get current user"""
    token = credentials.credentials

    if validate_with_service:
        # Call auth service
        auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{auth_service_url}/auth/validate",
                json={"token": token},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
    else:
        # Local validation
        jwt_secret = os.getenv("JWT_SECRET_KEY", "").strip().strip('"').strip("'")
        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=[os.getenv("JWT_ALGORITHM", "HS256")],
                options={
                    "verify_aud": False,
                    "verify_iat": False,
                }
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )


# ---------------------------------------------------------
# Permission Decorators
# ---------------------------------------------------------
from functools import wraps


def require_permission(permission: str):
    """Decorator to require specific permission"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request:
                # Try to find request in args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            auth = getattr(request.state, 'auth', None)
            if not auth or auth.get('type') != 'user':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User authentication required"
                )

            user_permissions = auth['payload'].get('permissions', [])
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires permission: {permission}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(role: str):
    """Decorator to require specific role"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            auth = getattr(request.state, 'auth', None)
            if not auth or auth.get('type') != 'user':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User authentication required"
                )

            user_roles = auth['payload'].get('roles', [])
            if role not in user_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires role: {role}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator