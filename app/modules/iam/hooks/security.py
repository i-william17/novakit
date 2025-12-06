import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import jwt
from passlib.context import CryptContext

from config.config import settings

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -----------------------------
# PASSWORD HELPERS
# -----------------------------
def hash_password(raw: str) -> str:
    return _pwd_ctx.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return _pwd_ctx.verify(raw, hashed)


# -----------------------------
# TOKEN EXPIRY
# -----------------------------
def get_access_token_expiry() -> datetime:
    minutes = 180 if settings.ENVIRONMENT == "local" else 30
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


# -----------------------------
# SECRET KEY
# -----------------------------
def get_secret_key() -> str:
    return hashlib.sha256(
        (settings.APP_ID + settings.SECRET_KEY).encode()
    ).hexdigest()


# -----------------------------
# JWT GENERATION
# -----------------------------
def generate_jwt_access_token(user: Any) -> str:
    expire = get_access_token_expiry()

    payload = {
        "sub": str(user.user_id),   # IMPORTANT
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": user.auth_key,
    }

    return jwt.encode(payload, get_secret_key(), algorithm="HS256")


def decode_jwt(token: str) -> Dict:
    return jwt.decode(
        token,
        get_secret_key(),
        algorithms=["HS256"],
        options={"verify_aud": False}
    )
