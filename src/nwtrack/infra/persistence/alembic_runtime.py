"""Programmatic Alembic configuration bound to an existing connection."""

from pathlib import Path

from alembic.config import Config
from sqlalchemy.engine import Connection

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def build_alembic_config(connection: Connection) -> Config:
    """Build an Alembic Config pointed at nwtrack's packaged migrations.

    Binds to an already-open SQLAlchemy connection rather than a URL, since
    nwtrack resolves its database location through ``Settings`` at runtime
    and never through a filesystem-discovered ``alembic.ini``.
    """
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.attributes["connection"] = connection
    return config
