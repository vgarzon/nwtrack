"""Tests for Alembic-backed schema migration via SchemaManager."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import inspect, select

from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.infra.config.settings import Settings
from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
from nwtrack.infra.persistence.orm.base import Base
from nwtrack.infra.persistence.orm.models import Account
from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

_EXPECTED_TABLES = {
    "currencies",
    "categories",
    "institutions",
    "tags",
    "accounts",
    "account_tags",
    "account_status_history",
    "balances",
    "exchange_rates",
    "alembic_version",
}


def _settings(tmp_path: Path, db_name: str) -> Settings:
    return Settings(
        db_file_path=str(tmp_path / db_name),
        log_file=str(tmp_path / "nwtrack-test.log"),
        log_file_level="INFO",
        log_rotation_mb=10,
        log_backup_count=7,
    )


def _create_legacy_database(db_path: Path) -> None:
    """Create a pre-institution_id schema (currencies/categories/accounts only)."""
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            PRAGMA foreign_keys=ON;

            CREATE TABLE currencies (
                code TEXT PRIMARY KEY,
                description TEXT NOT NULL
            );

            CREATE TABLE categories (
                name TEXT PRIMARY KEY,
                side TEXT NOT NULL CHECK(side IN ('asset', 'liability'))
            );

            CREATE TABLE accounts (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                category TEXT NOT NULL REFERENCES categories(name),
                currency TEXT NOT NULL REFERENCES currencies(code),
                status TEXT NOT NULL CHECK(status IN ('active', 'inactive'))
            );

            INSERT INTO currencies (code, description)
            VALUES ('USD', 'US Dollar');

            INSERT INTO categories (name, side)
            VALUES ('checking', 'asset');

            INSERT INTO accounts (id, name, description, category, currency, status)
            VALUES (1, 'cash', 'Legacy account', 'checking', 'USD', 'active');
            """
        )


def _sqlite_master_dump(db_path: Path) -> dict[str, str]:
    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT name, sql FROM sqlite_master "
            "WHERE type IN ('table', 'index') AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        ).fetchall()
    return dict(rows)


def _backup_files(tmp_path: Path) -> list[Path]:
    return sorted(tmp_path.glob("*.bak-*"))


def test_fresh_database_migrates_to_head_with_full_schema(tmp_path: Path) -> None:
    settings = _settings(tmp_path, "fresh.db")
    session_manager = SQLiteSessionManager(settings)
    schema_manager = SchemaManagerImpl(session_manager.engine)

    DBAdminService(settings, schema_manager).ensure_database()

    inspector = inspect(session_manager.engine)
    assert set(inspector.get_table_names()) == _EXPECTED_TABLES
    account_columns = {col["name"] for col in inspector.get_columns("accounts")}
    assert "institution_id" in account_columns


def test_legacy_database_upgrades_preserving_data(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    _create_legacy_database(db_path)

    settings = _settings(tmp_path, "legacy.db")
    session_manager = SQLiteSessionManager(settings)
    schema_manager = SchemaManagerImpl(session_manager.engine)

    DBAdminService(settings, schema_manager).ensure_database()

    inspector = inspect(session_manager.engine)
    assert set(inspector.get_table_names()) == _EXPECTED_TABLES
    account_columns = {col["name"] for col in inspector.get_columns("accounts")}
    assert "institution_id" in account_columns

    with session_manager.create_session() as session:
        accounts = list(session.execute(select(Account)).scalars())
    assert len(accounts) == 1
    assert accounts[0].name == "cash"
    assert accounts[0].institution_id is None


def test_legacy_database_upgrade_creates_backup(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy_backup.db"
    _create_legacy_database(db_path)

    settings = _settings(tmp_path, "legacy_backup.db")
    session_manager = SQLiteSessionManager(settings)
    schema_manager = SchemaManagerImpl(session_manager.engine)

    DBAdminService(settings, schema_manager).ensure_database()

    backups = _backup_files(tmp_path)
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as connection:
        rows = connection.execute("SELECT name FROM accounts").fetchall()
    assert rows == [("cash",)]


def test_already_current_untracked_database_stamps_without_schema_change(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "current.db"
    settings = _settings(tmp_path, "current.db")
    session_manager = SQLiteSessionManager(settings)

    Base.metadata.create_all(session_manager.engine)
    before = _sqlite_master_dump(db_path)

    schema_manager = SchemaManagerImpl(session_manager.engine)
    DBAdminService(settings, schema_manager).ensure_database()

    after = _sqlite_master_dump(db_path)
    after.pop("alembic_version", None)
    assert after == before
    assert _backup_files(tmp_path) == []


def test_ensure_current_schema_is_idempotent(tmp_path: Path) -> None:
    settings = _settings(tmp_path, "idempotent.db")
    session_manager = SQLiteSessionManager(settings)
    schema_manager = SchemaManagerImpl(session_manager.engine)
    service = DBAdminService(settings, schema_manager)

    service.ensure_database()
    db_path = tmp_path / "idempotent.db"
    after_first = _sqlite_master_dump(db_path)

    service.ensure_database()
    after_second = _sqlite_master_dump(db_path)

    assert after_first == after_second
    assert _backup_files(tmp_path) == []


def test_migration_failure_preserves_original_database(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy_fail.db"
    _create_legacy_database(db_path)
    before = _sqlite_master_dump(db_path)

    settings = _settings(tmp_path, "legacy_fail.db")
    session_manager = SQLiteSessionManager(settings)
    schema_manager = SchemaManagerImpl(session_manager.engine)

    with patch(
        "nwtrack.infra.persistence.schema.command.upgrade",
        side_effect=RuntimeError("boom"),
    ):
        with pytest.raises(RuntimeError, match=r"backup"):
            schema_manager.ensure_current_schema()

    after = _sqlite_master_dump(db_path)
    after.pop("alembic_version", None)
    assert after == before

    backups = _backup_files(tmp_path)
    assert len(backups) == 1


def _create_pre_display_order_database(db_path: Path, *, stamped: bool) -> None:
    """Create a 0002-shape accounts table with non-contiguous ids."""
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE currencies (code TEXT PRIMARY KEY, description TEXT NOT NULL);
            CREATE TABLE categories (
                name TEXT PRIMARY KEY,
                side TEXT NOT NULL CHECK(side IN ('asset', 'liability'))
            );
            CREATE TABLE institutions (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, description TEXT
            );
            CREATE TABLE accounts (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                category TEXT NOT NULL REFERENCES categories(name),
                currency TEXT NOT NULL REFERENCES currencies(code),
                status TEXT NOT NULL,
                institution_id INTEGER REFERENCES institutions(id),
                CONSTRAINT check_account_status
                    CHECK (status IN ('active', 'inactive'))
            );
            INSERT INTO currencies VALUES ('USD', 'US Dollar');
            INSERT INTO categories VALUES ('checking', 'asset');
            INSERT INTO accounts (id, name, description, category, currency, status)
            VALUES (2, 'b', '', 'checking', 'USD', 'active'),
                   (5, 'a', '', 'checking', 'USD', 'active'),
                   (9, 'c', '', 'checking', 'USD', 'inactive');
            """
        )
        if stamped:
            connection.executescript(
                """
                CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL);
                INSERT INTO alembic_version VALUES ('0002');
                """
            )


@pytest.mark.parametrize("stamped", [True, False])
def test_display_order_migration_backfills_by_id_rank(
    tmp_path: Path, stamped: bool
) -> None:
    db_path = tmp_path / "pre3.db"
    _create_pre_display_order_database(db_path, stamped=stamped)
    settings = _settings(tmp_path, "pre3.db")
    session_manager = SQLiteSessionManager(settings)
    schema_manager = SchemaManagerImpl(session_manager.engine)

    schema_manager.ensure_current_schema()

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT id, display_order, is_hidden, status FROM accounts ORDER BY id"
        ).fetchall()
    assert rows == [
        (2, 1, 0, "active"),
        (5, 2, 0, "active"),
        (9, 3, 0, "inactive"),
    ]
    assert len(_backup_files(tmp_path)) == 1
