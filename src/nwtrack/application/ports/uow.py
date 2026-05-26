"""
Unit of Work protocol
"""

from typing import Protocol

from nwtrack.application.ports.reporting import ReportingQueries
from nwtrack.application.ports.repos import (
    AccountsRepository,
    AccountStatusHistoryRepository,
    BalancesRepository,
    CategoriesRepository,
    CurrenciesRepository,
    ExchangeRatesRepository,
    InstitutionsRepository,
    NetWorthRepository,
    TagsRepository,
)


class UnitOfWork(Protocol):
    """Unit of Work protocol for managing database transactions."""

    currencies: CurrenciesRepository
    categories: CategoriesRepository
    institutions: InstitutionsRepository
    tags: TagsRepository
    accounts: AccountsRepository
    balances: BalancesRepository
    exchange_rates: ExchangeRatesRepository
    net_worth: NetWorthRepository
    account_status_history: AccountStatusHistoryRepository
    reporting: ReportingQueries
    _reporting: ReportingQueries

    def __enter__(self) -> "UnitOfWork": ...

    def __exit__(self, exc_type, exc_value, traceback) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
