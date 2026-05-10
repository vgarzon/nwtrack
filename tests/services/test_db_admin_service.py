"""Tests for database admin schema maintenance."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy import inspect, select

from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.infra.config.settings import Settings
from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
from nwtrack.infra.persistence.orm.models import Account, Institution
from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl


def test_ensure_database_upgrades_legacy_sqlite_schema(tmp_path: Path) -> None:
    """Existing SQLite files should be upgraded in place for institution support."""
    db_path = tmp_path / "legacy.db"
    _create_legacy_database(db_path)

    settings = Settings(db_file_path=str(db_path))
    session_manager = SQLiteSessionManager(settings)
    schema_manager = SchemaManagerImpl(session_manager.engine)
    service = DBAdminService(settings, schema_manager)

    service.ensure_database()
    service.ensure_database()

    with session_manager.create_session() as session:
        accounts = list(session.execute(select(Account)).scalars())
        institutions = list(session.execute(select(Institution)).scalars())

    assert len(accounts) == 1
    assert accounts[0].name == "cash"
    assert accounts[0].institution_id is None
    assert institutions == []


def test_ensure_database_creates_tag_tables_for_legacy_sqlite_schema(
    tmp_path: Path,
) -> None:
    """Existing SQLite files should gain tag tables through schema ensure."""
    db_path = tmp_path / "legacy_tags.db"
    _create_legacy_database(db_path)

    settings = Settings(db_file_path=str(db_path))
    session_manager = SQLiteSessionManager(settings)
    schema_manager = SchemaManagerImpl(session_manager.engine)
    service = DBAdminService(settings, schema_manager)

    service.ensure_database()
    service.ensure_database()

    inspector = inspect(session_manager.engine)

    assert "tags" in inspector.get_table_names()
    assert "account_tags" in inspector.get_table_names()
    assert {
        column["name"] for column in inspector.get_columns("account_tags")
    } == {"account_id", "tag_id"}


def _create_legacy_database(db_path: Path) -> None:
    """Create a pre-Phase-10 SQLite schema for regression testing."""
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
