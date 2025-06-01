"""
Database migration utilities for VMPilot.

This module provides functions to check and apply Alembic migrations
for the SQLite database schema.
"""

import logging
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)


def get_alembic_config(db_url: Optional[str] = None) -> Config:
    """
    Get Alembic configuration.

    Args:
        db_url: Database URL override. If None, uses the default from alembic.ini

    Returns:
        Alembic Config object
    """
    # Get the path to alembic.ini relative to this file
    db_dir = Path(__file__).parent
    alembic_ini_path = db_dir / "alembic.ini"
    migrations_dir = db_dir / "migrations"

    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"Alembic config not found at {alembic_ini_path}")

    # Create Alembic config
    alembic_cfg = Config(str(alembic_ini_path))

    # Set the migrations directory path
    alembic_cfg.set_main_option("script_location", str(migrations_dir))

    # Override database URL if provided
    if db_url:
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    return alembic_cfg


def get_current_revision(db_url: str) -> Optional[str]:
    """
    Get the current database revision.

    Args:
        db_url: Database URL

    Returns:
        Current revision ID or None if no migrations have been applied
    """
    try:
        engine = create_engine(db_url)
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            return context.get_current_revision()
    except Exception as e:
        logger.warning(f"Could not get current revision: {e}")
        return None


def get_head_revision() -> Optional[str]:
    """
    Get the head (latest) revision from migration scripts.

    Returns:
        Head revision ID or None if no migrations exist
    """
    try:
        alembic_cfg = get_alembic_config()
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        return script_dir.get_current_head()
    except Exception as e:
        logger.warning(f"Could not get head revision: {e}")
        return None


def check_migrations_needed(db_url: str) -> bool:
    """
    Check if database migrations are needed.

    Args:
        db_url: Database URL

    Returns:
        True if migrations are needed, False otherwise
    """
    current = get_current_revision(db_url)
    head = get_head_revision()

    if current is None and head is not None:
        logger.info("Database not initialized, migrations needed")
        return True

    if current != head:
        logger.info(
            f"Database at revision {current}, head is {head}, migrations needed"
        )
        return True

    logger.debug(f"Database up to date at revision {current}")
    return False


def apply_migrations(db_url: str) -> bool:
    """
    Apply pending database migrations.

    Args:
        db_url: Database URL

    Returns:
        True if migrations were applied successfully, False otherwise
    """
    try:
        logger.info("Applying database migrations...")
        alembic_cfg = get_alembic_config(db_url)

        # Apply migrations to head
        command.upgrade(alembic_cfg, "head")

        logger.info("Database migrations applied successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to apply migrations: {e}")
        return False


def ensure_database_migrated(db_url: str) -> bool:
    """
    Ensure the database is migrated to the latest version.

    This function checks if migrations are needed and applies them if so.

    Args:
        db_url: Database URL

    Returns:
        True if database is up to date, False if migration failed
    """
    try:
        if check_migrations_needed(db_url):
            return apply_migrations(db_url)
        else:
            logger.debug("Database already up to date")
            return True
    except Exception as e:
        logger.error(f"Error ensuring database migrated: {e}")
        return False
