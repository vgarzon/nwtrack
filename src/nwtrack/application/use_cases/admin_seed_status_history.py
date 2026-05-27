"""Seed account_status_history rows on demand."""

import logging

from nwtrack.application.dto import OperationResult, SeedStatusHistoryResult
from nwtrack.application.ports.presentation import AdminSeedStatusHistoryPresenter
from nwtrack.application.ports.schema import SchemaManager

logger = logging.getLogger(__name__)


class SeedAccountStatusHistory:
    """Seed account_status_history from balance history and current account status."""

    def __init__(
        self,
        schema_manager: SchemaManager,
        presenter: AdminSeedStatusHistoryPresenter,
    ) -> None:
        self._schema_manager = schema_manager
        self._presenter = presenter

    def run(self) -> OperationResult[SeedStatusHistoryResult]:
        logger.info("Starting SeedAccountStatusHistory use case")
        self._presenter.show_header()
        result = self._schema_manager.seed_account_status_history()
        self._presenter.show_result(result)
        logger.info(
            "Finished SeedAccountStatusHistory: seeded=%d migrated=%d skipped=%d",
            result.seeded, result.migrated, result.skipped,
        )
        return OperationResult(success=True, data=result)


def main() -> int:
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.application.ports.schema import SchemaManager as SchemaManagerPort
    from nwtrack.bootstrap.composition import build_base_container
    from nwtrack.bootstrap.container import Lifetime
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.admin_presenters import (
        RichAdminSeedStatusHistoryPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console
    from nwtrack.infra.db.sqlite.manager import SQLiteSessionManager
    from nwtrack.infra.persistence.schema import SchemaManager as SchemaManagerImpl

    load_dotenv()
    setup_logging()

    container = build_base_container()
    container.register(
        Console,
        lambda _: build_console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        SchemaManagerPort,
        lambda c: SchemaManagerImpl(engine=c.resolve(SQLiteSessionManager).engine),
    ).register(
        RichAdminSeedStatusHistoryPresenter,
        lambda c: RichAdminSeedStatusHistoryPresenter(console=c.resolve(Console)),
    ).register(
        SeedAccountStatusHistory,
        lambda c: SeedAccountStatusHistory(
            schema_manager=c.resolve(SchemaManagerPort),
            presenter=c.resolve(RichAdminSeedStatusHistoryPresenter),
        ),
    )

    op: OperationResult[SeedStatusHistoryResult] = (
        container.resolve(SeedAccountStatusHistory).run()
    )
    return 0 if op.success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
