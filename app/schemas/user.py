import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    photo_url: str | None = None
    font_size: str = "padrao"
    dark_mode: bool = False
    accessibility_profile: str | None = None
    streak: int = 0
    is_active: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    email: EmailStr | None = None
    password: str | None = Field(None, min_length=8)
    photo_url: str | None = None


class UserPreferencesRequest(BaseModel):
    font_size: str | None = Field(None, pattern="^(padrao|medio|grande)$")
    dark_mode: bool | None = None
    accessibility_profile: str | None = None
    rest_start: str | None = None
    rest_end: str | None = None
    motivational_time: str | None = None


class FCMTokenRequest(BaseModel):
    fcm_token: str
