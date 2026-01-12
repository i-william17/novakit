from contextvars import ContextVar
from typing import Optional
from app.modules.iam.models.user import User


# ContextVar stores per-request user identity
_current_user: ContextVar[Optional[User]] = ContextVar(
    "nova_current_user",
    default=None
)


class UserComponent:
    """Equivalent of Yii::$app->user"""

    @property
    def id(self) -> Optional[str]:
        user = _current_user.get()
        return user.user_id if user else None

    @property
    def identity(self) -> Optional[User]:
        return _current_user.get()

    @property
    def is_guest(self) -> bool:
        return _current_user.get() is None

    @property
    def is_authenticated(self) -> bool:
        return _current_user.get() is not None

    def set(self, user: Optional[User]):
        """Called by dependency when request resolves user identity"""
        _current_user.set(user)


class NovaApp:
    """Equivalent of Yii::$app"""
    def __init__(self):
        self.user = UserComponent()


# global instance (like Yii::$app)
nova = NovaApp()
