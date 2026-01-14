"""
Data transfer objects (DTOs).
"""

from dataclasses import dataclass
from nwtrack.domain.value_objects import Month
from nwtrack.domain.models import Category, Status


@dataclass(frozen=True)
class MonthlyCategoryBalance:
    """DTO for monthly balance total by category."""

    month: Month
    category: Category
    amount: int


@dataclass(frozen=True)
class NewAccountData:
    """Data class for new account creation use case."""

    account_name: str
    description: str
    category_name: str
    currency_code: str
    status: Status
    initial_month: Month
    initial_amount: int
