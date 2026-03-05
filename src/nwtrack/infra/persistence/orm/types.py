"""Custom SQLAlchemy type decorators."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, TypeDecorator

if TYPE_CHECKING:
    from sqlalchemy.engine import Dialect

from nwtrack.domain.value_objects import Month


class MonthType(TypeDecorator):
    """Custom type for Month value object.

    Stores Month as 'YYYY-MM' string in database, converts to/from Month object.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Month | None, dialect: Dialect) -> str | None:
        """Convert Month to string for database storage."""
        return str(value) if value else None

    def process_result_value(self, value: str | None, dialect: Dialect) -> Month | None:
        """Convert string from database to Month object."""
        return Month.parse(value) if value else None
