from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserPublic(BaseModel):
    user_id: int
    username: str
    profile_id: str
    status: int
    is_deleted: int
    created_at: int
    updated_at: int

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    username: str = Field(..., max_length=64)
    profile_id: str
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    username: Optional[str]
    profile_id: Optional[str]
    password: Optional[str]

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class Message(BaseModel):
    message: str
