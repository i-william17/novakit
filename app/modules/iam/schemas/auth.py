from pydantic import BaseModel, EmailStr, Field, field_validator
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.iam.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginInput(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordInput(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    def validate_strength(cls, v):
        import re
        if not re.match(r"^\S*(?=\S*[a-z])(?=\S*[A-Z])(?=\S*\d)(?=\S*\W)\S*$", v):
            raise ValueError(
                "Password must contain: 1 number, 1 lowercase, 1 uppercase, 1 special character"
            )
        return v

    @field_validator("confirm_new_password")
    def validate_match(cls, v, values):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class PasswordResetRequestInput(BaseModel):
    email: EmailStr


class ResetPasswordInput(BaseModel):
    password: str
