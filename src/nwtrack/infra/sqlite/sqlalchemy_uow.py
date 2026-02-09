"""
SQLAlchemy-based Unit of Work implementation.
"""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from nwtrack.application.ports.db import DBConnectionManager
from nwtrack.application.ports.uow import UnitOfWork


class SQLAlchemyUnitOfWork(UnitOfWork):
    """SQLAlchemy-based Unit of Work implementation.

    Manages database transactions using SQLAlchemy Session.
    Repositories are instantiated in __enter__() and share the same session.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        db_manager: DBConnectionManager | None = None,
    ):
        """Initialize UoW with session factory.

        Args:
            session_factory: Callable that creates new Session instances
            db_manager: Optional DBConnectionManager for legacy reporting queries
        """
        self._session_factory = session_factory
        self._session: Session | None = None
        self._db_manager = db_manager

    def __enter__(self) -> "SQLAlchemyUnitOfWork":
        """Enter context manager, create session and instantiate repositories."""
        self._session = self._session_factory()

        # Import repository implementations here to avoid circular imports
        from nwtrack.infra.sqlite.sqlalchemy_repos.accounts import (
            SQLAlchemyAccountsRepository,
        )
        from nwtrack.infra.sqlite.sqlalchemy_repos.balances import (
            SQLAlchemyBalancesRepository,
        )
        from nwtrack.infra.sqlite.sqlalchemy_repos.categories import (
            SQLAlchemyCategoriesRepository,
        )
        from nwtrack.infra.sqlite.sqlalchemy_repos.currencies import (
            SQLAlchemyCurrenciesRepository,
        )
        from nwtrack.infra.sqlite.sqlalchemy_repos.exchange_rates import (
            SQLAlchemyExchangeRatesRepository,
        )
        from nwtrack.infra.sqlite.sqlalchemy_repos.networth import (
            SQLAlchemyNetWorthRepository,
        )
        from nwtrack.infra.sqlite.reporting import SQLiteReportingQueries

        # Instantiate repositories with shared session
        self.currencies = SQLAlchemyCurrenciesRepository(self._session)
        self.categories = SQLAlchemyCategoriesRepository(self._session)
        self.accounts = SQLAlchemyAccountsRepository(self._session)
        self.balances = SQLAlchemyBalancesRepository(self._session)
        self.exchange_rates = SQLAlchemyExchangeRatesRepository(self._session)
        self.net_worth = SQLAlchemyNetWorthRepository(self._session)

        # Instantiate reporting queries with legacy db manager if provided
        if self._db_manager:
            self._reporting = SQLiteReportingQueries(self._db_manager)
        else:
            self._reporting = None  # type: ignore

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit context manager, commit or rollback based on exception."""
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        if self._session:
            self._session.close()

    def commit(self) -> None:
        """Commit the current transaction."""
        if self._session:
            self._session.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._session:
            self._session.rollback()
