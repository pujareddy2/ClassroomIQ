from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

UserRole = Literal["faculty", "admin", "reviewer"]


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole
    employee_id: str | None = Field(default=None, max_length=50)
    department_code: str | None = Field(default=None, max_length=50)
    department_name: str | None = Field(default=None, max_length=255)
    designation: str | None = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    profile_completed: bool = False
    institution: str | None = None
    department: str | None = None
    designation: str | None = None
    profile_image_url: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    institution: str | None = None
    department: str | None = None
    designation: str | None = None
    profile_image_url: str | None = None
