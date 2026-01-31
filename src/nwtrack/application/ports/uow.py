"""
Unit of Work protocol
"""

from typing import Protocol

from nwtrack.application.ports.reporting import ReportingQueries
from nwtrack.application.ports.repos import (
    AccountsRepository,
    BalancesRepository,
    CategoriesRepository,
    CurrenciesRepository,
    ExchangeRatesRepository,
    NetWorthRepository,
)


class UnitOfWork(Protocol):
    """Unit of Work protocol for managing database transactions."""

    currencies: CurrenciesRepository
    categories: CategoriesRepository
    accounts: AccountsRepository
    balances: BalancesRepository
    exchange_rates: ExchangeRatesRepository
    net_worth: NetWorthRepository
    _reporting: ReportingQueries

    def __enter__(self) -> "UnitOfWork": ...

    def __exit__(self, exc_type, exc_value, traceback) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
