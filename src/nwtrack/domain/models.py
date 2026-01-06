"""
Primary data models
"""

from dataclasses import dataclass
from enum import StrEnum
from nwtrack.domain.value_objects import Month


class Side(StrEnum):
    ASSET = "asset"
    LIABILITY = "liability"


class Status(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass
class Currency:
    code: str
    description: str


@dataclass
class Category:
    name: str
    side: Side


@dataclass
class Account:
    id: int
    name: str
    description: str
    category_name: str
    currency_code: str
    status: Status


@dataclass
class Balance:
    id: int
    account_id: int
    month: Month
    amount: int


@dataclass
class ExchangeRate:
    currency_code: str
    month: Month
    rate: float


@dataclass
class NetWorth:
    month: Month
    assets: int
    liabilities: int
    net_worth: int
    currency_code: str
