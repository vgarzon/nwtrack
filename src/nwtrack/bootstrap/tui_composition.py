"""
Dependency injection container setup for the TUI application.

Mirrors bootstrap/composition.py but does not modify the CLI composition root.
"""

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.application.services.fetch import FetchService
from nwtrack.application.use_cases.forward_fill_balances import ForwardFillBalances
from nwtrack.bootstrap.composition import build_base_container
from nwtrack.bootstrap.container import Container


def build_tui_container() -> Container:
    """Build DI container for the TUI application.

    Wires FetchService, ForwardFillBalances and UnitOfWork using the same SQLite
    infrastructure as the CLI composition root without modifying it.
    """
    container = build_base_container()
    container.register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        ForwardFillBalances,
        lambda c: ForwardFillBalances(
            uow=lambda: c.resolve(UnitOfWork),
            fetcher=c.resolve(FetchService),
        ),
    )
    return container
