from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
async def login(payload: LoginRequest) -> dict:
    return {
        "access_token": "scaffold-token",
        "token_type": "bearer",
        "email": payload.email,
        "message": "Authentication and JWT validation will be wired in the next phase.",
    }


@router.get("/me")
async def get_me() -> dict:
    return {
        "id": 1,
        "email": "admin@example.com",
        "role": "admin",
        "message": "Current-user lookup is a placeholder during scaffolding.",
    }

