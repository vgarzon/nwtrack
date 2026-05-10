"""
Data transfer objects (DTOs).
"""

from dataclasses import dataclass, field

from nwtrack.domain.models import Category, Institution, Status, Tag
from nwtrack.domain.value_objects import Month


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
    institution_id: int | None = None
    tag_ids: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class UpdatedAccountData:
    """Data class for account update workflow input."""

    account_id: int
    account_name: str
    description: str
    category_name: str
    currency_code: str
    status: Status
    institution_id: int | None = None
    tag_ids: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class InstitutionListItem:
    """Institution row for CLI administration views."""

    institution: Institution
    account_count: int


@dataclass(frozen=True)
class TagListItem:
    """Tag row for CLI administration views."""

    tag: Tag
    account_count: int


@dataclass(frozen=True)
class ValidationResult:
    """Result of validation operation."""

    is_valid: bool
    message: str = ""


@dataclass(frozen=True)
class OperationResult[T]:
    """Generic result of an operation."""

    success: bool
    data: T | None = None
    error_message: str = ""
