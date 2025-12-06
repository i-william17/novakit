from sqlalchemy_soft_delete import SoftDelete

class SoftDeleteMixin(SoftDelete):
    """Adds is_deleted + deleted_at fields and soft delete behavior."""
    pass
