import hashlib
from config.config import settings

def get_jwt_secret() -> str:
    return hashlib.sha256(
        f"{settings.APP_ID}:{settings.SECRET_KEY}".encode()
    ).hexdigest()
