import logging

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User
from app.repositories.user_repository import get_role_by_name, get_user_by_email

logger = logging.getLogger(__name__)

ROLE_DEFINITIONS = {
    "admin": "Manage watchlist, crawl runs, users, and roles.",
    "analyst": "Review categorizations, view dashboards, and export reports.",
    "viewer": "Read-only access to dashboards and reports.",
}


def ensure_default_access_control() -> None:
    if not settings.bootstrap_default_admin:
        return

    try:
        with SessionLocal() as db:
            changed = False
            role_cache: dict[str, Role] = {}

            for role_name, description in ROLE_DEFINITIONS.items():
                role = get_role_by_name(db, role_name)
                if role is None:
                    role = Role(name=role_name, description=description)
                    db.add(role)
                    db.flush()
                    changed = True
                role_cache[role_name] = role

            admin_user = get_user_by_email(db, settings.bootstrap_admin_email)
            if admin_user is None:
                admin_user = User(
                    full_name=settings.bootstrap_admin_name,
                    email=settings.bootstrap_admin_email,
                    password_hash=get_password_hash(settings.bootstrap_admin_password),
                    role_id=role_cache["admin"].id,
                    is_active=True,
                )
                db.add(admin_user)
                changed = True
            elif admin_user.role_id != role_cache["admin"].id:
                admin_user.role_id = role_cache["admin"].id
                changed = True

            if changed:
                db.commit()
    except SQLAlchemyError as exc:
        logger.warning("Skipping access-control bootstrap because the database is not ready: %s", exc)

