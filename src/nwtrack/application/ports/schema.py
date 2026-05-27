"""Schema management protocol."""

from typing import Protocol

from nwtrack.application.dto import SeedStatusHistoryResult


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

    def seed_account_status_history(self) -> SeedStatusHistoryResult:
        """Seed account_status_history rows from balance history and current status.

        Returns counts of accounts seeded, migrated, and skipped.
        """
        ...
