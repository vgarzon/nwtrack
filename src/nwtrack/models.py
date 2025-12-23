"""
Primary data models
"""

from dataclasses import dataclass
from enum import StrEnum


@dataclass
class Month:
    year: int
    month: int

    def __init__(self, year: int, month: int):
        if month < 1 or month > 12:
            raise ValueError(f"Invalid month: {month}")
        if year < 0:
            raise ValueError(f"Invalid year: {year}")
        self.year = year
        self.month = month

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    def __repr__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    @staticmethod
    def parse(s: str) -> "Month":
        year, month = map(int, s.split("-"))
        if "-" not in s or len(s.split("-")) != 2:
            raise ValueError(f"Invalid month format: {s}")
        if month < 1 or month > 12:
            raise ValueError(f"Invalid month: {month}")
        if year < 0:
            raise ValueError(f"Invalid year: {year}")
        return Month(year, month)

    def increment(self) -> "Month":
        if self.month == 12:
            return Month(self.year + 1, 1)
        else:
            return Month(self.year, self.month + 1)


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
