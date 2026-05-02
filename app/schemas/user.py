from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoogleTokenRequest(BaseModel):
    """Schema for Google OAuth token verification"""
    token: str


class GoogleTokenResponse(BaseModel):
    """Google token validation response"""
    sub: str
    email: EmailStr
    email_verified: bool
    name: str
    picture: str
    aud: str


class ProfileUpdateRequest(BaseModel):
    full_name: str
    password: str | None = None

