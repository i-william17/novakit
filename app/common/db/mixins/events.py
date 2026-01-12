from sqlalchemy import event
from app.common.db.sessions import get_db
from app.core.security import get_current_user_id

@event.listens_for(Base, "before_insert", propagate=True)
def before_insert(mapper, connection, target):
    if hasattr(target, "created_by"):
        try:
            target.created_by = get_current_user_id()
        except Exception:
            pass

@event.listens_for(Base, "before_update", propagate=True)
def before_update(mapper, connection, target):
    if hasattr(target, "updated_by"):
        try:
            target.updated_by = get_current_user_id()
        except Exception:
            pass
