"""
Export tables to csv files.
"""

import logging
from pathlib import Path

from nwtrack.application.ports.presentation import ExportTablesCSVPresenter
from nwtrack.application.services.export_csv import ExportCSV
from nwtrack.bootstrap.container import Container

logger = logging.getLogger(__name__)


class ExportTablesCSVBase:
    """Base class for exporting database tables to CSV files."""

    def __init__(self, exporter: ExportCSV, presenter: ExportTablesCSVPresenter) -> None:
        self._exporter = exporter
        self._presenter = presenter

    def create_target_path(self, target_path: Path) -> bool:
        """Create the target directory for CSV export."""
        logger.info("Creating directory %s.", target_path)
        self._presenter.show_creating_directory(target_path)
        try:
            target_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("Failed to create directory %s: %s", target_path, str(e))
            self._presenter.show_directory_create_error(target_path, str(e))
            return False
        return True

    def export_tables_to_dir(self, target_dir: Path) -> None:
        """Export database tables to CSV files in the target directory."""
        export_summary = self._exporter.export_tables_to_dir(target_dir)
        for table_name, csv_path, n_records in export_summary:
            if n_records == 0:
                self._presenter.show_table_skipped(table_name)
                continue
            self._presenter.show_table_exported(table_name, csv_path, n_records)


class ExportTablesCSVInteractive(ExportTablesCSVBase):
    """Export database tables to CSV files."""

    def run(self, defaults: dict) -> None:
        """Run the export process."""
        logger.info("Starting Export Tables to CSV files.")
        self._presenter.show_header()
        try:
            target_dir = self.collect_target_dir(defaults=defaults)
        except KeyboardInterrupt:
            self._presenter.show_cancellation()
            return
        self.export_tables_to_dir(target_dir)
        logger.info("Finished exporting tables to CSV files.")

    def collect_target_dir(self, defaults: dict) -> Path:
        """Collect and validate target directory from user input."""
        while True:
            target_dir = self._presenter.prompt_for_target_dir(
                default=defaults.get("target_dir", "")
            )
            if target_dir.lower() == "q":
                logger.warning("User aborted csv export target directory input")
                raise KeyboardInterrupt
            target_path = Path(target_dir)
            if target_path.is_dir():
                return target_path

            create = self._presenter.confirm_create_directory(target_dir)
            if create:
                success = self.create_target_path(target_path)
                if success:
                    return target_path


class ExportTablesCSVCLI(ExportTablesCSVBase):
    """Export database tables to CSV files via CLI."""

    def run(self, target_dir: str, create: bool = False) -> None:
        """Run the export process."""
        logger.info("Starting Export Tables to CSV files.")
        self._presenter.show_header()
        target_path, valid = self.check_or_create_target_dir(target_dir, create)
        if not valid:
            logger.error("Invalid target directory %s. Aborting export.", target_dir)
            return
        self.export_tables_to_dir(target_path)
        logger.info("Finished exporting tables to CSV files.")

    def check_or_create_target_dir(
        self, target_dir: str, create: bool
    ) -> tuple[Path, bool]:
        """Check or create the target directory for CSV export."""
        target_path = Path(target_dir)
        if target_path.exists() and not target_path.is_dir():
            logger.error("Target path %s is not a directory.", target_path)
            self._presenter.show_not_a_directory_error(target_path)
            return target_path, False
        if not target_path.exists() and not create:
            logger.error("Target directory %s does not exist.", target_path)
            self._presenter.show_directory_not_found_error(target_path)
            return target_path, False
        success = self.create_target_path(target_path)
        return target_path, success


def bootstrap() -> Container:
    from dotenv import load_dotenv

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.composition import build_base_container
    from nwtrack.bootstrap.logging_config import setup_logging
    from nwtrack.entrypoints.cli.adapters.csv_presenters import (
        RichExportTablesCSVPresenter,
    )
    from nwtrack.entrypoints.cli.ui.console import build_console

    load_dotenv()
    setup_logging()
    container = build_base_container()
    container.register(
        ExportCSV,
        lambda c: ExportCSV(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        ExportTablesCSVPresenter,  # type: ignore[type-abstract]
        lambda c: RichExportTablesCSVPresenter(console=build_console()),
    )
    return container


def run_interactive(container: Container, defaults: dict) -> None:
    """Run export in interactive mode."""
    container.register(
        ExportTablesCSVInteractive,
        lambda c: ExportTablesCSVInteractive(
            exporter=c.resolve(ExportCSV),
            presenter=c.resolve(ExportTablesCSVPresenter),  # type: ignore[type-abstract]
        ),
    )
    container.resolve(ExportTablesCSVInteractive).run(defaults)


def run_cli(container: Container, target_dir: str, create: bool) -> None:
    """Run export in CLI mode."""
    container.register(
        ExportTablesCSVCLI,
        lambda c: ExportTablesCSVCLI(
            exporter=c.resolve(ExportCSV),
            presenter=c.resolve(ExportTablesCSVPresenter),  # type: ignore[type-abstract]
        ),
    )
    container.resolve(ExportTablesCSVCLI).run(target_dir=target_dir, create=create)


if __name__ == "__main__":
    import sys

    container: Container = bootstrap()

    argv = sys.argv[1:]
    if not argv:
        run_interactive(container, defaults={})
    else:
        target_dir = argv[0]
        create_flag = "--create" in argv
        run_cli(container, target_dir=target_dir, create=create_flag)
