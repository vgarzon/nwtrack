"""
Database initializer services
"""

import logging

from nwtrack.application.dto import OperationResult
from nwtrack.application.ports.presentation import DBInitCSVPresenter
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.infra.config.settings import Settings

logger = logging.getLogger(__name__)


class DBInitializerCSV:
    """Initialize the database from CSV files."""

    def __init__(
        self,
        config: Settings,
        admin_svc: DBAdminService,
        data_svc: InitDataService,
        presenter: DBInitCSVPresenter,
    ) -> None:
        self._config = config
        self._admin_svc = admin_svc
        self._data_svc = data_svc
        self._presenter = presenter
        # TODO: Use RepoRegistry to specify required keys
        self._required_keys = [
            "currencies",
            "categories",
            "accounts",
            "balances",
            "exchange_rates",
        ]
        self._file_paths: dict[str, str] = {}

    def run(self) -> OperationResult[None]:
        """Run the database initialization process."""
        logger.info("Starting database initialization from CSV files.")
        logger.info("Database file path: %s", self._config.db_file_path)
        self._presenter.show_header(self._config.db_file_path)
        try:
            self._file_paths = self._presenter.prompt_for_file_paths(
                self._required_keys
            )
        except KeyboardInterrupt:
            logging.warning("User aborted csv file input.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Aborted by user")

        self._presenter.show_file_paths_table(self._file_paths)
        accept = self._presenter.prompt_for_confirmation()
        if not accept:
            logger.warning("User aborted database initialization.")
            self._presenter.show_cancellation()
            return OperationResult(success=False, error_message="Aborted by user")

        try:
            self._admin_svc.init_database()
        except Exception as e:
            logger.error("Database initialization failed: %s", e)
            self._presenter.show_error(f"Database initialization failed: {e}")
            return OperationResult(success=False, error_message=str(e))

        try:
            self._data_svc.insert_data_from_csv(self._file_paths)
        except Exception as e:
            logger.error("Data insertion from CSV files failed: %s", e)
            self._presenter.show_error(f"Data insertion failed: {e}")
            return OperationResult(success=False, error_message=str(e))

        self._presenter.show_success()
        logger.info("Finished database initialization from CSV files.")
        return OperationResult(success=True)


def main() -> int:
    """Main entry point for DB initialization from CSV files.

    Returns:
        int: Exit code, 0 for success, non-zero for failure
    """
    from dotenv import load_dotenv
    from rich.console import Console

    from nwtrack.application.ports.presentation import DBInitCSVPresenter
    from nwtrack.application.ports.schema import SchemaManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.composition import Lifetime, build_base_container
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.db_admin_presenters import (
        RichDBInitCSVPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import ConsoleSettings
    from nwtrack.entrypoints.cli.ui.factory import ConsoleFactory
    from nwtrack.infra.sqlite.sqlalchemy_manager import SQLAlchemySessionManager
    from nwtrack.infra.sqlite.sqlalchemy_schema_manager import SQLAlchemySchemaManager

    load_dotenv()
    setup_logging()

    console_defaults = ConsoleSettings(record=False)

    container = build_base_container()
    container.register(
        SchemaManager,
        lambda c: SQLAlchemySchemaManager(
            engine=c.resolve(SQLAlchemySessionManager).engine
        ),
    ).register(
        DBAdminService,
        lambda c: DBAdminService(c.resolve(Settings), c.resolve(SchemaManager)),
    ).register(
        InitDataService,
        lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        Console,
        lambda c: ConsoleFactory(default_settings=console_defaults)(),
    ).register(
        DBInitCSVPresenter,
        lambda c: RichDBInitCSVPresenter(console=c.resolve(Console)),
        lifetime=Lifetime.SINGLETON,
    ).register(
        DBInitializerCSV,
        lambda c: DBInitializerCSV(
            config=c.resolve(Settings),
            admin_svc=c.resolve(DBAdminService),
            data_svc=c.resolve(InitDataService),
            presenter=c.resolve(DBInitCSVPresenter),
        ),
    )
    result: OperationResult[None] = container.resolve(DBInitializerCSV).run()

    return 0 if result.success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
