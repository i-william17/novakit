from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class ProfileResponse(BaseModel):
    first_name: str
    middle_name: Optional[str]
    last_name: str
    email_address: EmailStr
    phone_number: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user_id: UUID
    username: str
    status: int
    profile: ProfileResponse

    class Config:
        from_attributes = True
