from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str
    profile_id: Optional[str] = None


class UserOut(UserBase):
    user_id: uuid.UUID
    status: int
    profile_id: Optional[str]

    class Config:
        from_attributes = True
