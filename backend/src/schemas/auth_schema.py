from pydantic import BaseModel, EmailStr, Field, field_validator

from src.schemas.user_schema import UserResponse


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2)
    password: str = Field(min_length=8)
    role: str = "analyst"

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        allowed = {"analyst", "admin"}
        role = value.strip().lower()
        if role not in allowed:
            raise ValueError(f"role must be one of: {sorted(allowed)}.")
        return role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
