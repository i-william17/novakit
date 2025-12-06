import jwt
from jwt import InvalidTokenError
from config.config import settings

def decode_jwt(token: str):
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except InvalidTokenError:
        return None
