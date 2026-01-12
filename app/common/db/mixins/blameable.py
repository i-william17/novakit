from sqlalchemy import Column, Integer

class BlameableMixin:
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
