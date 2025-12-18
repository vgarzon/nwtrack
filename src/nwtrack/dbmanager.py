"""
Relational database manager module.
"""

from __future__ import annotations

import sqlite3
from typing import Protocol, TypeAlias, Any
from collections.abc import Sequence, Mapping

from nwtrack.config import Config

DBAPIConnection: TypeAlias = sqlite3.Connection
SQLiteValue: TypeAlias = str | int | float | bytes | None
ParamMapping: TypeAlias = Mapping[str, SQLiteValue]
ParamSequence: TypeAlias = Sequence[SQLiteValue]


class DBConnectionManager(Protocol):
    """Database connection manager protocol."""

    def get_connection(self) -> DBAPIConnection: ...

    def execute(
        self, sql: str, params: ParamMapping | ParamSequence | None = None
    ) -> Any: ...

    def script(self, sql: str) -> None: ...

    def execute_many(self, query: str, params: list[dict] = []) -> int: ...

    def fetch_all(self, query: str, params: dict = {}) -> list[dict]: ...

    def fetch_one(self, query: str, params: dict = {}) -> dict | None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def close_connection(self) -> None: ...


class SQLiteConnectionManager:
    """SQLite database connection manager."""

    def __init__(self, config: Config) -> None:
        self._db_file_path: str = config.db_file_path
        self._connection: DBAPIConnection | None = None

    def get_connection(self) -> DBAPIConnection:
        if self._connection is None:
            self._create_connection()
        assert self._connection is not None, "Database connection unavailable."
        return self._connection

    def _create_connection(self) -> DBAPIConnection:
        print("Creating new SQLite connection.")
        conn = sqlite3.connect(self._db_file_path)
        conn.execute("PRAGMA foreign_keys = ON;")  # NOTE: Enabled in DDL script too
        conn.row_factory = sqlite3.Row
        self._connection = conn
        return conn

    def execute(
        self, sql: str, params: ParamMapping | ParamSequence | None = None
    ) -> sqlite3.Cursor:
        conn = self.get_connection()

        if params is None:
            cursor = conn.execute(sql)
        else:
            cursor = conn.execute(sql, params)

        conn.commit()
        return cursor

    def script(self, sql: str) -> None:
        with self.get_connection() as conn:
            conn.executescript(sql)
            conn.commit()

    def execute_many(self, query: str, params: list[dict] = []) -> int:
        with self.get_connection() as conn:
            cursor = conn.executemany(query, params)
            rowcount = cursor.rowcount
        return rowcount

    def fetch_all(self, query: str, params: dict = {}) -> list[dict]:
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            results = cursor.fetchall()
        return results

    def fetch_one(self, query: str, params: dict = {}) -> dict | None:
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            result = cursor.fetchone()
        return result

    def commit(self) -> None:
        with self.get_connection() as conn:
            conn.commit()

    def rollback(self) -> None:
        with self.get_connection() as conn:
            conn.rollback()

    def close_connection(self) -> None:
        print("Closing SQLite connection.")
        if self._connection:
            self._connection.close()
            self._connection = None
