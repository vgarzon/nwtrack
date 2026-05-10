"""
Data transfer objects (DTOs).
"""

from dataclasses import dataclass, field
from enum import StrEnum

from nwtrack.domain.models import Category, Institution, Status, Tag
from nwtrack.domain.value_objects import Month


class AggregationDimension(StrEnum):
    """Supported account-attribute dimensions for grouped balance reporting."""

    CATEGORY = "category"
    SIDE = "side"
    INSTITUTION = "institution"
    CURRENCY = "currency"
    TAG = "tag"


class AccountStatusScope(StrEnum):
    """Status filter applied to shared aggregation queries."""

    ACTIVE = "active"
    ALL = "all"


@dataclass(frozen=True)
class MonthlyCategoryBalance:
    """DTO for monthly balance total by category."""

    month: Month
    category: Category
    amount: int


@dataclass(frozen=True)
class SingleMonthAggregationRequest:
    """Application-level request for one month of grouped balance totals."""

    month: Month
    dimension: AggregationDimension
    currency_code: str | None = None
    status_scope: AccountStatusScope = AccountStatusScope.ACTIVE


@dataclass(frozen=True)
class SingleMonthAggregationGroup:
    """One grouped balance row from the shared aggregation layer."""

    group_key: str
    label: str
    amount: int
    currency_code: str


@dataclass(frozen=True)
class SingleMonthAggregationResult:
    """Result of single-month grouped balance aggregation."""

    month: Month
    dimension: AggregationDimension
    currency_code: str | None
    status_scope: AccountStatusScope
    groups: list[SingleMonthAggregationGroup]


@dataclass(frozen=True)
class HistoryAggregationRequest:
    """Application-level request for grouped totals across an inclusive month range."""

    start_month: Month
    end_month: Month
    dimension: AggregationDimension
    currency_code: str | None = None
    status_scope: AccountStatusScope = AccountStatusScope.ACTIVE


@dataclass(frozen=True)
class HistoryAggregationRow:
    """One grouped balance row for one month in a history aggregation result."""

    month: Month
    group_key: str
    label: str
    amount: int
    currency_code: str


@dataclass(frozen=True)
class HistoryAggregationResult:
    """Result of grouped balance aggregation across an inclusive month range."""

    start_month: Month
    end_month: Month
    dimension: AggregationDimension
    currency_code: str | None
    status_scope: AccountStatusScope
    rows: list[HistoryAggregationRow]


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
class AccountUpdateData:
    """Data class for interactive account updates."""

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
