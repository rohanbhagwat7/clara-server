"""Authentication data models"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class GoogleLoginRequest(BaseModel):
    """Request to login with Google ID token"""
    id_token: str


class TokenRefreshRequest(BaseModel):
    """Request to refresh access token"""
    refresh_token: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int
    user: 'UserProfile'


class UserProfile(BaseModel):
    """User profile information"""
    user_id: str
    email: str
    full_name: str
    role: str
    profile_picture_url: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class UserCreate(BaseModel):
    """User creation data"""
    email: EmailStr
    full_name: str
    google_id: str
    role: str = "technician"
    profile_picture_url: Optional[str] = None
