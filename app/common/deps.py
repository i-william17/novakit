from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import InvalidTokenError
from config.config import settings

security = HTTPBearer(auto_error=False)  # do not auto raise; let us control

def get_current_user_from_state(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Optional: decode directly from Authorization header if not using middleware.
    But prefer get_current_user_from_state when middleware is active.
    """
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")



# @route("get", "/me")
# async def me(self, request: Request, current_user = Depends(get_current_user_from_state)):
#     return {"me": current_user}
