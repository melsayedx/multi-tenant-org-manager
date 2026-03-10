import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=32)
    full_name: str = Field(min_length=1, max_length=64)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError(
                "Password must contain at least one uppercase letter, e.g. A-Z"
            )
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number, e.g. 0-9")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError(
                "Password must contain at least one special character, e.g. !@#$%^&*"
            )
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
