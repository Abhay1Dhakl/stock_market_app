from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    last_login_at: Optional[datetime] = None
    role: str

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if hasattr(obj, "role") and not isinstance(getattr(obj, "role", None), str):
            payload = {
                "id": obj.id,
                "full_name": obj.full_name,
                "email": obj.email,
                "is_active": obj.is_active,
                "last_login_at": obj.last_login_at,
                "role": obj.role.name,
            }
            return super().model_validate(payload, *args, **kwargs)
        return super().model_validate(obj, *args, **kwargs)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in_minutes: int
    user: UserProfile
