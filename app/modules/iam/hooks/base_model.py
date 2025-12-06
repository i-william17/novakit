from app.common.base.base_model import BaseModel
from app.common.utils.status_mixin import StatusMixin


class IamBaseModel(BaseModel, StatusMixin):
    __abstract__ = True

    # extra IAM features here
    def soft_delete(self):
        self.is_deleted = True

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
