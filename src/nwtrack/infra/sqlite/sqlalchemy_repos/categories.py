"""
SQLAlchemy implementation of Categories repository.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from nwtrack.application.ports.repos import CategoriesRepository
from nwtrack.infra.sqlite.orm_models import Category

logger = logging.getLogger(__name__)


class SQLAlchemyCategoriesRepository(CategoriesRepository):
    """SQLAlchemy-based repository for categories operations."""

    def __init__(self, session: Session):
        """Initialize repository with SQLAlchemy session.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self._session = session

    def insert(self, data: Category) -> int:
        """Insert a category into database.

        Args:
            data: Category object

        Returns:
            Number of inserted rows
        """
        self._session.add(data)
        self._session.flush()
        logger.info("Inserted 1 category row.")
        return 1

    def insert_many(self, data: list[Category]) -> None:
        """Insert list of categories into database.

        Args:
            data: List of Category objects
        """
        self._session.add_all(data)
        self._session.flush()
        logger.info("Inserted %d category rows.", len(data))

    def get(self, name: str) -> Category | None:
        """Get category by name.

        Args:
            name: Category name

        Returns:
            Category object if found, else None
        """
        return self._session.execute(
            select(Category).where(Category.name == name)
        ).scalar_one_or_none()

    def get_all(self) -> list[Category]:
        """Get all Categories.

        Returns:
            List of category objects
        """
        result = self._session.execute(select(Category)).scalars()
        return list(result)

    def get_dict(self) -> dict[str, Category]:
        """Get all categories in a dictionary indexed by name.

        Returns:
            Dictionary of categories records indexed by name
        """
        categories = self.get_all()
        return {category.name: category for category in categories}

    def count(self) -> int:
        """Count the number of category records.

        Returns:
            Number of category records
        """
        result = self._session.execute(
            select(func.count()).select_from(Category)
        ).scalar()
        return result or 0

    def delete_all(self) -> None:
        """Delete all category records."""
        result = self._session.execute(delete(Category))
        logger.info("Deleted %d category records.", result.rowcount)  # type: ignore[attr-defined]

    def hydrate(self, record: Mapping[str, Any]) -> Category:
        """Hydrate record to Category entity.

        Args:
            record: Data dictionary

        Returns:
            Category object
        """
        from nwtrack.infra.sqlite.orm_models import Side

        return Category(name=record["name"], side=Side(record["side"]))

    def hydrate_many(self, data: list[Mapping[str, Any]]) -> list[Category]:
        """Hydrate list of records to list of Category entities.

        Args:
            data: List of data dictionaries

        Returns:
            List of Category objects
        """
        return [self.hydrate(record) for record in data]
