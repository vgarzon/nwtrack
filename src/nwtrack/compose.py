"""
Common dependency injection container setup for NWTrack application.
"""

from nwtrack.config import Config, load_config
from nwtrack.dbmanager import DBConnectionManager, SQLiteConnectionManager
from nwtrack.repos import (
    SQLiteCurrencyRepository,
    SQLiteAccountTypeRepository,
    SQLiteExchangeRateRepository,
    SQLiteAccountRepository,
    SQLiteBalanceRepository,
    NwTrackRepository,
)
from nwtrack.services import NWTrackService
from nwtrack.admin import AdminService
from nwtrack.container import Container, Lifetime


def setup_basic_container() -> Container:
    """Setup basic container with common dependencies.

    Returns:
        Container: Configured DI container.
    """
    print("Setting up dependency container.")
    container = Container()
    container.register(
        Config,
        lambda _: load_config(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        DBConnectionManager,
        lambda c: SQLiteConnectionManager(c.resolve(Config)),
        lifetime=Lifetime.SINGLETON,
    ).register(
        SQLiteCurrencyRepository,
        lambda c: SQLiteCurrencyRepository(c.resolve(DBConnectionManager)),
    ).register(
        SQLiteAccountTypeRepository,
        lambda c: SQLiteAccountTypeRepository(c.resolve(DBConnectionManager)),
    ).register(
        SQLiteExchangeRateRepository,
        lambda c: SQLiteExchangeRateRepository(c.resolve(DBConnectionManager)),
    ).register(
        SQLiteAccountRepository,
        lambda c: SQLiteAccountRepository(c.resolve(DBConnectionManager)),
    ).register(
        SQLiteBalanceRepository,
        lambda c: SQLiteBalanceRepository(c.resolve(DBConnectionManager)),
    ).register(
        NwTrackRepository,
        lambda c: NwTrackRepository(c.resolve(DBConnectionManager)),
    ).register(
        AdminService,
        lambda c: AdminService(c.resolve(Config), c.resolve(DBConnectionManager)),
        lifetime=Lifetime.SINGLETON,
    ).register(
        NWTrackService,
        lambda c: NWTrackService(
            currency_repo=c.resolve(SQLiteCurrencyRepository),
            account_types_repo=c.resolve(SQLiteAccountTypeRepository),
            exchange_rate_repo=c.resolve(SQLiteExchangeRateRepository),
            account_repo=c.resolve(SQLiteAccountRepository),
            balance_repo=c.resolve(SQLiteBalanceRepository),
            repo=c.resolve(NwTrackRepository),
        ),
    )
    return container
