"""
Import tables from CSV files.
"""

import logging
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt

from nwtrack.application.services.data_loader import InitDataService
from nwtrack.application.services.db_admin import DBAdminService
from nwtrack.bootstrap.container import Container
from nwtrack.entrypoints.cli.ui.console import build_console

logger = logging.getLogger(__name__)


class ImportTablesCSVBase:
    """Base class for importing database tables from CSV files."""

    def __init__(
        self,
        importer: InitDataService,
        admin_svc: DBAdminService,
        console: Console,
    ) -> None:
        self._importer = importer
        self._admin_svc = admin_svc
        self._console = console

    def import_tables_from_dir(self, source_dir: Path) -> None:
        """Import database tables from CSV files in the source directory."""
        try:
            self._admin_svc.ensure_database()
            self._importer.import_bundle_from_dir(source_dir)
        except Exception as exc:
            logger.error("Failed to import CSV bundle from %s: %s", source_dir, exc)
            self._console.print(f"[error]Error:[/error] {exc}")
            return
        self._console.print(
            f"[success]Imported[/success] CSV tables from [bold]{source_dir}[/bold]"
        )


class ImportTablesCSVInteractive(ImportTablesCSVBase):
    """Import database tables to the runtime database."""

    def __init__(
        self,
        importer: InitDataService,
        admin_svc: DBAdminService,
        console: Console,
    ) -> None:
        super().__init__(importer, admin_svc, console)
        self._prompt = Prompt(console=self._console)

    def run(self, defaults: dict[str, str]) -> None:
        """Run the import process."""
        logger.info("Starting Import Tables from CSV files.")
        self._console.rule("[header]Import Tables from CSV[/header]")
        try:
            source_dir = self.collect_source_dir(defaults=defaults)
        except KeyboardInterrupt:
            self._console.print("[cancel]CSV import aborted by user.[/cancel]")
            return
        self.import_tables_from_dir(source_dir)
        logger.info("Finished importing tables from CSV files.")

    def collect_source_dir(self, defaults: dict[str, str]) -> Path:
        """Collect source directory from user input."""
        source_dir = self._prompt.ask(
            "[label]Please enter source directory or 'q' to quit[/label]",
            default=defaults.get("source_dir", ""),
        ).strip()
        if source_dir.lower() == "q":
            logger.warning("User aborted csv import source directory input")
            raise KeyboardInterrupt
        return Path(source_dir)


class ImportTablesCSVCLI(ImportTablesCSVBase):
    """Import database tables to the runtime database via CLI."""

    def run(self, source_dir: str) -> None:
        """Run the import process."""
        logger.info("Starting Import Tables from CSV files.")
        self._console.rule("[header]Import Tables from CSV[/header]")
        self.import_tables_from_dir(Path(source_dir))
        logger.info("Finished importing tables from CSV files.")


def bootstrap() -> Container:
    from dotenv import load_dotenv

    from nwtrack.bootstrap.composition import (
        build_base_container,
        build_data_services_container,
    )
    from nwtrack.bootstrap.logging_config import setup_logging

    load_dotenv()
    setup_logging()
    container = build_data_services_container(build_base_container())
    container.register(
        Console,
        lambda c: build_console(),
    )
    return container


def run_interactive(container: Container, defaults: dict[str, str]) -> None:
    """Run import in interactive mode."""
    container.register(
        ImportTablesCSVInteractive,
        lambda c: ImportTablesCSVInteractive(
            importer=c.resolve(InitDataService),
            admin_svc=c.resolve(DBAdminService),
            console=c.resolve(Console),
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
            console=c.resolve(Console),
        ),
    )
    container.resolve(ImportTablesCSVCLI).run(source_dir=source_dir)
