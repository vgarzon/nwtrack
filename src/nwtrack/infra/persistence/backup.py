"""Pre-migration backup for file-backed SQLite databases."""

import logging
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def backup_before_migration(engine: Engine) -> Path | None:
    """Snapshot a file-backed SQLite database before an actual schema change.

    Uses SQLite's ``VACUUM INTO`` to produce a consistent on-disk copy
    regardless of journal mode, run over a dedicated autocommit connection
    since ``VACUUM`` cannot execute inside a transaction. Returns ``None``
    (no-op) for ``:memory:`` or other non-file databases.
    """
    db_url = engine.url
    database = db_url.database
    if db_url.get_backend_name() != "sqlite" or not database or database == ":memory:":
        return None

    db_path = Path(database)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_path = db_path.with_name(f"{db_path.name}.bak-{timestamp}")

    logger.info(
        "Backing up database to '%s' before applying schema migration.",
        backup_path,
    )
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql("VACUUM INTO ?", (str(backup_path),))
    return backup_path
