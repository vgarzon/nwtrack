"""
SQLAlchemy-based Unit of Work implementation.
"""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from nwtrack.application.ports.uow import UnitOfWork


class SQLAlchemyUnitOfWork(UnitOfWork):
    """SQLAlchemy-based Unit of Work implementation.

    Manages database transactions using SQLAlchemy Session.
    Repositories are instantiated in __enter__() and share the same session.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
    ):
        """Initialize UoW with session factory.

        Args:
            session_factory: Callable that creates new Session instances
        """
        self._session_factory = session_factory
        self._session: Session | None = None

    def __enter__(self) -> SQLAlchemyUnitOfWork:
        """Enter context manager, create session and instantiate repositories."""
        self._session = self._session_factory()

        # Import repository implementations here to avoid circular imports
        from nwtrack.infra.persistence.repositories.accounts import (
            AccountsRepository,
        )
        from nwtrack.infra.persistence.repositories.balances import (
            BalancesRepository,
        )
        from nwtrack.infra.persistence.repositories.categories import (
            CategoriesRepository,
        )
        from nwtrack.infra.persistence.repositories.currencies import (
            CurrenciesRepository,
        )
        from nwtrack.infra.persistence.repositories.exchange_rates import (
            ExchangeRatesRepository,
        )
        from nwtrack.infra.persistence.repositories.institutions import (
            InstitutionsRepository,
        )
        from nwtrack.infra.persistence.repositories.networth import (
            NetWorthRepository,
        )
        from nwtrack.infra.persistence.repositories.reporting import (
            ReportingQueries,
        )

        # Instantiate repositories with shared session
        self.currencies = CurrenciesRepository(self._session)
        self.categories = CategoriesRepository(self._session)
        self.institutions = InstitutionsRepository(self._session)
        self.accounts = AccountsRepository(self._session)
        self.balances = BalancesRepository(self._session)
        self.exchange_rates = ExchangeRatesRepository(self._session)
        self.net_worth = NetWorthRepository(self._session)
        self._reporting = ReportingQueries(self._session)

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
