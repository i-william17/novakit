from pydantic import BaseModel, EmailStr, validator, field_validator, model_validator
from typing import Optional
import uuid
import re


class UserBase(BaseModel):
    username: str


class ProfileCreate(BaseModel):
    first_name: str
    middle_name: str | None = None
    last_name: str
    email_address: EmailStr
    phone_number: str

    @field_validator("first_name", "middle_name", "last_name", mode="before")
    @classmethod
    def validate_name(cls, value: str | None):
        if value is None:
            return value

        # Only letters and apostrophe
        if not re.fullmatch(r"[a-zA-Z']+", value):
            raise ValueError("Name can only contain alphabetic characters")

        # No 3+ consecutive identical characters
        if re.search(r"(.)\1{2,}", value):
            raise ValueError(
                "Name cannot contain three or more consecutive identical characters"
            )

        return value

    # @field_validator("username", mode="before")
    # @classmethod
    # def normalize_username(cls, value: str):
    #     return value.strip().lower()

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str):
        pattern = r"^(07|01|\+2547|\+2541)[0-9]{8}$"

        if not re.fullmatch(pattern, value):
            raise ValueError("Invalid phone number")

        return value

class UserCreate(UserBase):
    password: str
    confirm_password: str
    profile: ProfileCreate

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[0-9]", value):
            raise ValueError("Password must contain at least one number")

        if not re.search(r"[!@#$%^&*()_\-+=\[{\]};:'\",.<>/?\\|`~]", value):
            raise ValueError("Password must contain at least one special character")

        return value

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class ProfileOut(BaseModel):
    first_name: str
    middle_name: str | None
    last_name: str
    email_address: EmailStr
    phone_number: str

    class Config:
        orm_mode = True

class UserOut(UserBase):
    user_id: uuid.UUID
    status: int
    profile_id: Optional[str]
    profile: ProfileOut

    class Config:
        from_attributes = True
