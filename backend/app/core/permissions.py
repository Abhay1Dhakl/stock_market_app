from enum import Enum
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class Role(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    return {
        "id": 1,
        "email": "admin@example.com",
        "role": Role.ADMIN,
        "token": token,
    }


def require_role(*allowed_roles: Role) -> Callable:
    def dependency(user: dict = Depends(get_current_user)) -> dict:
        user_role = Role(user["role"])
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return user

    return dependency

