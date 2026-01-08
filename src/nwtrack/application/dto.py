"""
Data transfer objects (DTOs).
"""

from dataclasses import dataclass
from nwtrack.domain.value_objects import Month
from nwtrack.domain.models import Category


@dataclass(frozen=True)
class MonthlyCategoryBalance:
    """DTO for monthly balance total by category."""

    month: Month
    category: Category
    amount: int
