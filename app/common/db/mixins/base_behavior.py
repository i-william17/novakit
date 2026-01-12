from .timestamp import TimestampMixin
from .soft_delete import SoftDeleteMixin
from .blameable import BlameableMixin

class BaseBehaviorMixin(
    TimestampMixin,
    SoftDeleteMixin,
    BlameableMixin,
):
    """Default behaviors applied to most models"""
    pass
