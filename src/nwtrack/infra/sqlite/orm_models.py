"""
SQLAlchemy ORM models for nwtrack entities.

These models use MappedAsDataclass to maintain dataclass behavior while
providing ORM capabilities. This allows domain entities to work as both
dataclasses and SQLAlchemy models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    String,
    TypeDecorator,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column

if TYPE_CHECKING:
    from sqlalchemy.engine import Dialect

# Import enums from domain
from enum import StrEnum

from nwtrack.domain.value_objects import Month


class Side(StrEnum):
    """Accounting side for categories."""

    ASSET = "asset"
    LIABILITY = "liability"


class Status(StrEnum):
    """Account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class MonthType(TypeDecorator):
    """Custom type for Month value object.

    Stores Month as 'YYYY-MM' string in database, converts to/from Month object.
    """

    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: Month | None, dialect: Dialect
    ) -> str | None:
        """Convert Month to string for database storage."""
        return str(value) if value else None

    def process_result_value(
        self, value: str | None, dialect: Dialect
    ) -> Month | None:
        """Convert string from database to Month object."""
        return Month.parse(value) if value else None


class Currency(MappedAsDataclass, Base):
    """Currency entity."""

    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[str] = mapped_column(String)


class Category(MappedAsDataclass, Base):
    """Category entity."""

    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("side IN ('asset', 'liability')", name="check_category_side"),
    )

    name: Mapped[str] = mapped_column(String, primary_key=True)
    side: Mapped[Side] = mapped_column(
        SQLEnum(Side, values_callable=lambda x: [e.value for e in x])
    )


class Account(MappedAsDataclass, Base):
    """Account entity."""

    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive')", name="check_account_status"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str] = mapped_column(String)
    category_name: Mapped[str] = mapped_column(
        "category", String, ForeignKey("categories.name")
    )
    currency_code: Mapped[str] = mapped_column(
        "currency", String, ForeignKey("currencies.code"), default="USD"
    )
    status: Mapped[Status] = mapped_column(
        SQLEnum(Status, values_callable=lambda x: [e.value for e in x]),
        default=Status.ACTIVE,
    )


class Balance(MappedAsDataclass, Base):
    """Balance entity."""

    __tablename__ = "balances"
    __table_args__ = (
        UniqueConstraint("account_id", "month", name="uq_balance_account_month"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("accounts.id")
    )
    month: Mapped[Month] = mapped_column(MonthType)
    amount: Mapped[int] = mapped_column(Integer)


class ExchangeRate(MappedAsDataclass, Base):
    """Exchange rate entity."""

    __tablename__ = "exchange_rates"
    __table_args__ = (
        UniqueConstraint("currency", "month", name="uq_exchange_rate_currency_month"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    currency_code: Mapped[str] = mapped_column(
        "currency", String, ForeignKey("currencies.code")
    )
    month: Mapped[Month] = mapped_column(MonthType)
    rate: Mapped[float] = mapped_column(Float)


@dataclass
class NetWorth:
    """NetWorth computed entity (DTO for aggregation results).

    This is not an ORM model - it represents computed aggregation data
    from Balance/Account/Category joins.
    """

    month: Month
    currency_code: str
    assets: int
    liabilities: int
    net_worth: int
