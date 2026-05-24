"""
Import tables from CSV files.
"""

import logging
from pathlib import Path

from nwtrack.application.ports.presentation import ImportTablesCSVPresenter
from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.bootstrap.container import Container

logger = logging.getLogger(__name__)


class ImportTablesCSVBase:
    """Base class for importing database tables from CSV files."""

    def __init__(
        self,
        importer: InitDataService,
        admin_svc: DBAdminService,
        presenter: ImportTablesCSVPresenter,
    ) -> None:
        self._importer = importer
        self._admin_svc = admin_svc
        self._presenter = presenter

    def import_tables_from_dir(self, source_dir: Path) -> None:
        """Import database tables from CSV files in the source directory."""
        try:
            self._admin_svc.ensure_database()
            self._importer.import_bundle_from_dir(source_dir)
        except Exception as exc:
            logger.error("Failed to import CSV bundle from %s: %s", source_dir, exc)
            self._presenter.show_error(str(exc))
            return
        self._presenter.show_import_success(source_dir)


class ImportTablesCSVInteractive(ImportTablesCSVBase):
    """Import database tables to the runtime database."""

    def run(self, defaults: dict[str, str]) -> None:
        """Run the import process."""
        logger.info("Starting Import Tables from CSV files.")
        self._presenter.show_header()
        try:
            source_dir = self.collect_source_dir(defaults=defaults)
        except KeyboardInterrupt:
            self._presenter.show_cancellation()
            return
        self.import_tables_from_dir(source_dir)
        logger.info("Finished importing tables from CSV files.")

    def collect_source_dir(self, defaults: dict[str, str]) -> Path:
        """Collect source directory from user input."""
        source_dir = self._presenter.prompt_for_source_dir(
            default=defaults.get("source_dir", "")
        )
        if source_dir.lower() == "q":
            logger.warning("User aborted csv import source directory input")
            raise KeyboardInterrupt
        return Path(source_dir)


class ImportTablesCSVCLI(ImportTablesCSVBase):
    """Import database tables to the runtime database via CLI."""

    def run(self, source_dir: str) -> None:
        """Run the import process."""
        logger.info("Starting Import Tables from CSV files.")
        self._presenter.show_header()
        self.import_tables_from_dir(Path(source_dir))
        logger.info("Finished importing tables from CSV files.")


def bootstrap() -> Container:
    from dotenv import load_dotenv

    from nwtrack.bootstrap.composition import (
        build_base_container,
        build_data_services_container,
    )
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.csv_presenters import (
        RichImportTablesCSVPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    load_dotenv()
    setup_logging()
    container = build_data_services_container(build_base_container())
    container.register(
        ImportTablesCSVPresenter,  # type: ignore[type-abstract]
        lambda c: RichImportTablesCSVPresenter(console=build_console()),
    )
    return container


def run_interactive(container: Container, defaults: dict[str, str]) -> None:
    """Run import in interactive mode."""
    container.register(
        ImportTablesCSVInteractive,
        lambda c: ImportTablesCSVInteractive(
            importer=c.resolve(InitDataService),
            admin_svc=c.resolve(DBAdminService),
            presenter=c.resolve(ImportTablesCSVPresenter),  # type: ignore[type-abstract]
        ),
    )
    container.resolve(ImportTablesCSVInteractive).run(defaults)


def run_cli(container: Container, source_dir: str) -> None:
    """Run import in CLI mode."""
    container.register(
        ImportTablesCSVCLI,
        lambda c: ImportTablesCSVCLI(
            importer=c.resolve(InitDataService),
            admin_svc=c.resolve(DBAdminService),
            presenter=c.resolve(ImportTablesCSVPresenter),  # type: ignore[type-abstract]
        ),
    )
    container.resolve(ImportTablesCSVCLI).run(source_dir=source_dir)
