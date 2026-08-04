from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.core.config import settings

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = PROJECT_ROOT / "alembic.ini"
ALEMBIC_SCRIPT_PATH = PROJECT_ROOT / "alembic"


@retry(
    stop=stop_after_attempt(10),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def run_database_migrations() -> None:
    if settings.environment == "test":
        return

    alembic_config = Config(str(ALEMBIC_INI_PATH))
    alembic_config.set_main_option("script_location", str(ALEMBIC_SCRIPT_PATH))
    alembic_config.set_main_option("sqlalchemy.url", settings.database_url)

    logger.info("Applying database migrations from %s", ALEMBIC_SCRIPT_PATH)
    command.upgrade(alembic_config, "head")
