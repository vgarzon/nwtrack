"""List accounts with no institution assigned."""

import logging

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import AdminListUnassignedPresenter
from nwtrack.application.services.fetch import FetchService

logger = logging.getLogger(__name__)


class ListUnassignedAccounts:
    """List accounts that have no institution assigned."""

    def __init__(
        self,
        fetcher: FetchService,
        presenter: AdminListUnassignedPresenter,
    ) -> None:
        self._fetcher = fetcher
        self._presenter = presenter

    def run(self) -> OperationResult[None]:
        logger.info("Starting ListUnassignedAccounts use case")
        accounts = self._fetcher.get_accounts_without_institution()
        if accounts:
            self._presenter.display_unassigned(accounts)
        else:
            self._presenter.show_empty_state()
        logger.info("Finished ListUnassignedAccounts")
        return OperationResult(success=True)


def main() -> int:
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.composition import build_base_container
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.admin_presenters import (
        RichAdminListUnassignedPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    load_dotenv()
    setup_logging()

    container = build_base_container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        RichAdminListUnassignedPresenter,
        lambda c: RichAdminListUnassignedPresenter(console=c.resolve(Console)),
    ).register(
        ListUnassignedAccounts,
        lambda c: ListUnassignedAccounts(
            fetcher=c.resolve(FetchService),
            presenter=c.resolve(RichAdminListUnassignedPresenter),
        ),
    )

    result: OperationResult[None] = container.resolve(ListUnassignedAccounts).run()
    return 0 if result.success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
