from app.common.base.base_model import BaseModel

class IamBaseModel(BaseModel):
    __abstract__ = True

    # extra IAM features here
    def soft_delete(self):
        self.is_deleted = True

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
