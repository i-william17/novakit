import hashlib
from typing import Callable, Set, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from config.config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that protects all routes by default and excludes configured SAFE_ENDPOINTS.
    Add to app with: app.add_middleware(AuthMiddleware, safe_endpoints=...)
    """

    def __init__(
        self,
        app: ASGIApp,
        safe_endpoints: Optional[Set[str]] = None,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        allow_cookie_refresh: bool = True,
    ):
        super().__init__(app)
        # prefer passed safe_endpoints then settings.SAFE_ENDPOINTS (if any)
        if safe_endpoints is not None:
            self.safe_endpoints = set(safe_endpoints)
        else:
            self.safe_endpoints = settings.safe_endpoints

        # self.secret_key = secret_key or settings.JWT_SECRET_KEY
        self.secret_key = (secret_key or settings.JWT_SECRET_KEY).strip().strip('"').strip("'")
        self.algorithm = algorithm or getattr(settings, "JWT_ALGORITHM", "HS256")
        self.allow_cookie_refresh = allow_cookie_refresh

        # add API prefix variants and normalize
        self._add_api_prefix_to_safe_endpoints()
        self.safe_endpoints = self._normalize_endpoints(self.safe_endpoints)

    def _add_api_prefix_to_safe_endpoints(self):
        api_prefix = getattr(settings, "API_V1_STR", "/v1")
        new = set()
        for ep in self.safe_endpoints:
            if not ep:
                continue
            if ep.startswith(api_prefix) or ep in {"/", "/docs", "/openapi.json", "/redoc"}:
                new.add(ep)
            else:
                norm = ep if ep.startswith("/") else f"/{ep}"
                new.add(norm)
                new.add(f"{api_prefix}{norm}")
        self.safe_endpoints = new

    def _normalize_endpoints(self, endpoints: Set[str]) -> Set[str]:
        normalized = set()
        for e in endpoints:
            if e != "/" and e.endswith("/"):
                normalized.add(e.rstrip("/"))
            else:
                normalized.add(e)
        return normalized

    def _is_safe_endpoint(self, path: str) -> bool:
        normalized = path.rstrip("/") if path != "/" else "/"

        # exact match
        if normalized in self.safe_endpoints:
            return True

        # explicit wildcard-safe paths only
        for safe in self.safe_endpoints:
            if safe.endswith("/*"):
                base = safe[:-2]
                if normalized == base or normalized.startswith(base + "/"):
                    return True

        return False

    def _extract_token(self, request: Request) -> Optional[str]:
        auth: Optional[str] = request.headers.get("Authorization")
        if auth:
            parts = auth.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                # return parts[1]
                return parts[1].strip()
        # fallback: cookie (if enabled)
        if self.allow_cookie_refresh:
            cookie = request.cookies.get("access_token") or request.cookies.get("refresh_token")
            if cookie:
                return cookie
        return None

    def _validate_token(self, token: str) -> dict:
        try:
            # print("JWT SECRET USED:", self.secret_key)
            # print("JWT TOKEN:", token)
            # print(
            #     "MW SECRET:",
            #     repr(self.secret_key),
            #     "HASH:",
            #     hashlib.sha256(self.secret_key.encode()).hexdigest()
            # )

            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={
                "verify_aud": False,
                "verify_iat": False,
            })
            # print("JWT PAYLOAD:", payload)
            return payload
        except ExpiredSignatureError as ex:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        except InvalidTokenError as e:
            # print(f"DECODE ERROR: {str(e)}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    async def dispatch(self, request: Request, call_next: Callable):
        # allow OPTIONS and docs/health etc
        path = request.url.path

        if path in {"/", "/favicon.ico"}:
            return await call_next(request)

        if self._is_safe_endpoint(path):
            return await call_next(request)

        token = self._extract_token(request)
        if not token:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Authentication required"})

        try:
            payload = self._validate_token(token)

            # attach full auth context for downstream usage
            request.state.auth = {
                "payload": payload,
                "token": token,
                "ip": request.client.host if request.client else None,
                "ua": request.headers.get("User-Agent"),
            }

            request.state.jwt_payload = payload
            request.state.jwt_token = token

            # backward-compat shortcut
            request.state.user = payload
            return await call_next(request)
        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except Exception:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Internal server error"})







