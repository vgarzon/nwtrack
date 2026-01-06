"""
Mapper protocol for converting between databaes ecords and entities.
"""

from __future__ import annotations

from typing import Protocol, Any, TypeVar

TEntity = TypeVar("TEntity")

SQLiteRecord = dict[str, Any]


class Mapper(Protocol[TEntity]):
    """A mapper to convert records to and from entities."""

    def to_entity(self, record: SQLiteRecord) -> TEntity:
        """Convert a record to an entity.

        Args:
            record: The record to convert.

        Returns:
            The converted entity.
        """
        ...

    def to_record(self, entity: TEntity) -> SQLiteRecord:
        """Convert an entity to a record.

        Args:
            entity: The entity to convert.

        Returns:
            The converted record.
        """
        ...
