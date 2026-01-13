import hashlib
import jwt
import httpx
from typing import Optional, Set, Dict, Any, Callable
from functools import wraps, lru_cache
from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import os
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger("shared.auth")


# ---------------------------------------------------------
# Service-to-Service Authentication
# ---------------------------------------------------------
class ServiceAuth:
    """Handles authentication between microservices"""

    def __init__(self):
        self.auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
        self.service_secret = os.getenv("SERVICE_SECRET", "")
        self.service_name = os.getenv("SERVICE_NAME", "")

    async def validate_service_token(self, token: str) -> Dict[str, Any]:
        """Validate service-to-service token"""
        try:
            # For now, use simple secret validation
            # In production, use proper JWT or mTLS
            if token != self.service_secret:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid service token"
                )

            return {
                "service": self.service_name,
                "authenticated": True
            }
        except Exception as e:
            logger.error(f"Service token validation failed: {e}")
            raise

    async def get_service_token(self) -> str:
        """Get token for calling other services"""
        # Generate a simple token for now
        # In production, get from auth service
        timestamp = int(datetime.utcnow().timestamp())
        token_data = f"{self.service_name}:{timestamp}:{self.service_secret}"
        return hashlib.sha256(token_data.encode()).hexdigest()[:32]


# ---------------------------------------------------------
# Client Authentication Middleware
# ---------------------------------------------------------
class MicroserviceAuthMiddleware(BaseHTTPMiddleware):
    """
    Enhanced auth middleware for microservices
    Supports both client JWT and service-to-service authentication
    """

    def __init__(
            self,
            app: ASGIApp,
            safe_endpoints: Optional[Set[str]] = None,
            allow_service_auth: bool = True,
            validate_with_auth_service: bool = True
    ):
        super().__init__(app)

        self.safe_endpoints = safe_endpoints or {
            "/health", "/docs", "/openapi.json", "/redoc",
            "/metrics", "/healthz", "/readyz"
        }

        self.allow_service_auth = allow_service_auth
        self.validate_with_auth_service = validate_with_auth_service
        self.auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")

        # JWT configuration
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "").strip().strip('"').strip("'")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")

        # Service authentication
        self.service_auth = ServiceAuth()

        # Cache for token validation
        self.token_cache = {}

    def _is_safe_endpoint(self, path: str) -> bool:
        """Check if endpoint is safe (no auth required)"""
        normalized = path.rstrip("/") if path != "/" else "/"
        return normalized in self.safe_endpoints

    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract token from request"""
        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:].strip()

        # Check X-Service-Token header (for service-to-service)
        service_token = request.headers.get("X-Service-Token")
        if service_token:
            return service_token

        # Check cookies
        cookie_token = request.cookies.get("access_token")
        if cookie_token:
            return cookie_token

        return None

    async def _validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token"""
        try:
            # Check cache first
            cache_key = hashlib.md5(token.encode()).hexdigest()
            if cache_key in self.token_cache:
                cached = self.token_cache[cache_key]
                if datetime.utcnow().timestamp() < cached["expires"]:
                    return cached["payload"]

            # Validate with auth service if enabled
            if self.validate_with_auth_service:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        f"{self.auth_service_url}/auth/validate",
                        json={"token": token},
                        headers={"Content-Type": "application/json"}
                    )

                    if response.status_code == 200:
                        payload = response.json()
                        # Cache the result (5 minutes)
                        self.token_cache[cache_key] = {
                            "payload": payload,
                            "expires": datetime.utcnow().timestamp() + 300
                        }
                        return payload

            # Fallback to local JWT validation
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                options={
                    "verify_aud": False,
                    "verify_iat": False,
                }
            )

            # Cache the result
            self.token_cache[cache_key] = {
                "payload": payload,
                "expires": datetime.utcnow().timestamp() + 300
            }

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
        except httpx.RequestError:
            # If auth service is down, fallback to local validation
            try:
                payload = jwt.decode(
                    token,
                    self.jwt_secret,
                    algorithms=[self.jwt_algorithm],
                    options={
                        "verify_aud": False,
                        "verify_iat": False,
                    }
                )
                return payload
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token validation failed: {str(e)}"
                )

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip auth for safe endpoints
        path = request.url.path
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
            if self.allow_service_auth and request.headers.get("X-Service-Token"):
                payload = await self.service_auth.validate_service_token(token)
                auth_type = "service"
            else:
                payload = await self._validate_jwt_token(token)
                auth_type = "user"

            # Attach auth context to request
            request.state.auth = {
                "payload": payload,
                "type": auth_type,
                "token": token,
                "authenticated": True,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Backward compatibility
            if auth_type == "user":
                request.state.user = payload

            return await call_next(request)

        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(f"Auth middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )


# ---------------------------------------------------------
# Permission Decorators
# ---------------------------------------------------------
def require_permission(permission: str):
    """Decorator to require specific permission"""

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
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

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_role(role: str):
    """Decorator to require specific role"""

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
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

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


# ---------------------------------------------------------
# FastAPI Dependency for auth
# ---------------------------------------------------------
security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        auth_service_url: str = Depends(lambda: os.getenv("AUTH_SERVICE_URL"))
) -> Dict[str, Any]:
    """FastAPI dependency to get current user"""
    token = credentials.credentials

    try:
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
    except httpx.RequestError:
        # Fallback to local validation if auth service is unavailable
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