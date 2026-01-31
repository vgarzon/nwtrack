"""
Relational database manager module.
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterable, Mapping, Sequence

from nwtrack.infra.config.settings import Settings

logger = logging.getLogger(__name__)

type SQLiteValue = str | int | float | bool | bytes | None
type SQLiteParamMapping = Mapping[str, SQLiteValue]
type SQLiteParamSequence = Sequence[SQLiteValue]
type SQLiteParamSet = SQLiteParamMapping | SQLiteParamSequence
type SQLiteManyParams = Iterable[SQLiteParamSet]


class SQLiteConnectionManager:
    """SQLite database connection manager."""

    def __init__(self, config: Settings) -> None:
        self._db_file_path: str = config.db_file_path
        self._connection: sqlite3.Connection | None = None

    def get_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self._create_connection()
        assert self._connection is not None, "Database connection unavailable."
        return self._connection

    def _create_connection(self) -> sqlite3.Connection:
        logger.info("Creating SQLite connection to '%s'", self._db_file_path)
        conn = sqlite3.connect(self._db_file_path)
        conn.execute("PRAGMA foreign_keys = ON;")  # TODO: Enable in DDL script
        conn.row_factory = sqlite3.Row
        self._connection = conn
        return conn

    def execute(self, sql: str, params: SQLiteParamSet | None = None) -> sqlite3.Cursor:
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

    def execute_many(self, query: str, params: SQLiteManyParams) -> int:
        with self.get_connection() as conn:
            cursor = conn.executemany(query, params)
            rowcount = cursor.rowcount
        return rowcount

    def fetch_all(
        self, query: str, params: SQLiteParamSet | None = None
    ) -> list[Mapping[str, SQLiteValue]]:
        with self.get_connection() as conn:
            if params is None:
                cursor = conn.execute(query)
            else:
                cursor = conn.execute(query, params)
            results = cursor.fetchall()
        return results

    def fetch_one(
        self, query: str, params: SQLiteParamSet | None = None
    ) -> Mapping[str, SQLiteValue] | None:
        with self.get_connection() as conn:
            if params is None:
                cursor = conn.execute(query)
            else:
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
        logger.info("Closing SQLite connection.")
        if self._connection:
            self._connection.close()
            self._connection = None
