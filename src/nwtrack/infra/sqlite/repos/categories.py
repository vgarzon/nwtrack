"""
SQLite implementation of the Categories repository.
"""

from __future__ import annotations

from nwtrack.domain.models import Category
from nwtrack.application.ports.repos import BaseRepository


class SQLiteCategoriesRepository(BaseRepository[Category]):
    """Repository for category SQLite database operations."""

    def insert_many(self, data: list[Category]) -> None:
        """Insert list of categories into SQLite database.

        Args:
            data (list[Category]): List of category data dictionaries.
        """
        rowcount = self._db.execute_many(
            "INSERT INTO categories (name, side) VALUES (:name, :side);",
            [self._mapper.to_record(record) for record in data],
        )
        print("Inserted", rowcount, "category rows.")

    def get(self, name: str) -> Category | None:
        """Get category by name.

        Args:
            name (str): Category name.

        Returns:
            Category | None: Category object if found, else None.
        """
        query = "SELECT name, side FROM categories WHERE name = :name;"
        result = self._db.fetch_one(query, {"name": name})
        if result:
            return self._mapper.to_entity(result)
        else:
            return None

    def get_all(self) -> list[Category]:
        """Get all Categories.

        Returns:
            list[Category]: List of category objects.
        """
        query = "SELECT name, side FROM categories;"
        results = self._db.fetch_all(query)
        return [self._mapper.to_entity(record) for record in results]

    def get_dict(self) -> dict[str, Category]:
        """Get all categories in a dictionary indexed by code.

        Returns:
            dict[str, Category]: Dictionary of categories records indexed by name.
        """
        results = self.get_all()
        categories = {result.name: result for result in results}
        return categories

    def count(self) -> int:
        """Count the number of category records.

        Returns:
            int: Number of category records.
        """
        query = "SELECT COUNT(*) AS cnt FROM categories;"
        result = self._db.fetch_one(query)
        return result["cnt"] if result else 0

    def delete_all(self) -> None:
        """Delete all category records."""
        query = "DELETE FROM categories;"
        cur = self._db.execute(query)
        print(f"Deleted {cur.rowcount} category records.")
