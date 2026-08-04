from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.role import Role
from app.models.user import User


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    statement = (
        select(User)
        .options(joinedload(User.role))
        .where(func.lower(User.email) == email.strip().lower())
    )
    return db.scalar(statement)


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    statement = select(User).options(joinedload(User.role)).where(User.id == user_id)
    return db.scalar(statement)


def get_role_by_name(db: Session, role_name: str) -> Optional[Role]:
    return db.scalar(select(Role).where(Role.name == role_name))


def list_users(db: Session) -> list[User]:
    statement = select(User).options(joinedload(User.role)).order_by(User.full_name.asc())
    return list(db.scalars(statement).unique().all())
