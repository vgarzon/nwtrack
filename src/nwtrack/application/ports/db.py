"""
Database protocols.
"""

from __future__ import annotations

import sqlite3
from typing import Protocol, TypeAlias, Any
from collections.abc import Sequence, Mapping

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
