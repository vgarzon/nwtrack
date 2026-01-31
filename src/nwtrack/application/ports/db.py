"""
Database protocols.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Protocol

type ParamValue = str | int | float | bool | bytes | None
type ParamMapping = Mapping[str, ParamValue]
type ParamSequence = Sequence[ParamValue]
type ParamSet = ParamMapping | ParamSequence
type ManyParams = Iterable[ParamSet]


class DBConnectionManager(Protocol):
    """Database connection manager protocol."""

    def get_connection(self) -> Any: ...

    def execute(self, sql: str, params: ParamSet | None = None) -> Any: ...

    def script(self, sql: str) -> None: ...

    def execute_many(self, query: str, params: ManyParams) -> int: ...

    def fetch_all(
        self, query: str, params: ParamSet | None = None
    ) -> list[Mapping[str, ParamValue]]: ...

    def fetch_one(
        self, query: str, params: ParamSet | None = None
    ) -> Mapping[str, Any] | None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def close_connection(self) -> None: ...
