"""
Value objects: Immutable types that represent specific concepts.
No behavior beyond data storage and simple operations.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Month:
    year: int
    month: int

    def __init__(self, year: int, month: int):
        if month < 1 or month > 12:
            logging.error("Attempted to create Month with invalid month: %d", month)
            raise ValueError(f"Invalid month: {month}")
        if year < 0:
            logging.error("Attempted to create Month with invalid year: %d", year)
            raise ValueError(f"Invalid year: {year}")
        self.year = year
        self.month = month

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    def __repr__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Month):
            return NotImplemented
        return self.year == other.year and self.month == other.month

    def __hash__(self) -> int:
        """Make Month hashable for use in sets, dicts, and composite keys."""
        return hash((self.year, self.month))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Month):
            return NotImplemented
        if self.year != other.year:
            return self.year < other.year
        return self.month < other.month

    @staticmethod
    def parse(s: str) -> "Month":
        year, month = map(int, s.split("-"))
        if "-" not in s or len(s.split("-")) != 2:
            logger.error("Attempted to parse Month from invalid string: %s", s)
            raise ValueError(f"Invalid month format: {s}")
        if month < 1 or month > 12:
            logger.error("Attempted to parse Month with invalid month: %d", month)
            raise ValueError(f"Invalid month: {month}")
        if year < 0:
            logger.error("Attempted to parse Month with invalid year: %d", year)
            raise ValueError(f"Invalid year: {year}")
        return Month(year, month)

    def increment(self) -> "Month":
        if self.month == 12:
            return Month(self.year + 1, 1)
        else:
            return Month(self.year, self.month + 1)
