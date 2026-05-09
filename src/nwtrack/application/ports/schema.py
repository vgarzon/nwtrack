"""Schema management protocol."""

from typing import Protocol


class SchemaManager(Protocol):
    """Protocol for database schema operations.

    Abstracts underlying engine/metadata implementation.
    """

    def drop_all_tables(self) -> None:
        """Drop all tables (destructive operation)."""
        ...

    def create_all_tables(self) -> None:
        """Create all tables from ORM definitions."""
        ...

    def ensure_current_schema(self) -> None:
        """Bring an existing database up to the current supported schema."""
        ...
