from __future__ import annotations

from typing import Optional

from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.repositories.user_repository import get_user_by_email
from app.schemas.auth import TokenResponse, UserProfile


def authenticate_user(db, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def build_token_response(user: User) -> TokenResponse:
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"role": user.role.name, "email": user.email},
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_minutes=60,
        user=UserProfile.model_validate(user),
    )
