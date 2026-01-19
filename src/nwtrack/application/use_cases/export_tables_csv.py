"""
Export tables to csv files.
"""

import logging
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt

from nwtrack.application.services.export_csv import ExportCSV

logger = logging.getLogger(__name__)


class ExportTablesCSVDir:
    """Export database tables to CSV files."""

    def __init__(self, exporter: ExportCSV, console: Console) -> None:
        self._exporter = exporter
        self._console = console
        self._prompt = Prompt(console=self._console)
        self._confirm = Confirm(console=self._console)

    def run(self) -> None:
        """Run the export process."""
        logger.info("Starting Export Tables to CSV files.")
        self._console.rule("[bold green]Export Tables to CSV[/bold green]")
        try:
            target_dir = self.collect_target_dir()
        except KeyboardInterrupt:
            self._console.print("[red]CSV export aborted by user.[/red]")
            return
        self.export_tables_to_dir(target_dir)
        logger.info("Finished exporting tables to CSV files.")

    def collect_target_dir(self) -> Path:
        """Collect and validate target directory from user input.

        Returns:
            target_dir (Path): Validated target directory path.
        Exceptions:
            KeyboardInterrupt: if user interrupts input
        """
        while True:
            dir_str = self._prompt.ask(
                "[yellow]Please enter target directory or 'q' to quit[/yellow]"
            ).strip()
            if dir_str.lower() == "q":
                logger.warning("User aborted csv export target directory input")
                raise KeyboardInterrupt
            target_dir = Path(dir_str)
            if target_dir.is_dir():
                return target_dir

            create = self._confirm.ask(
                f"[red]Directory [/red][bold]{dir_str}[/bold] "
                "[red]does not exist. Create it?[/red]",
                default=False,
            )
            if create:
                try:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    self._console.print(f"[green]Created directory[/green]: {dir_str}")
                    return target_dir
                except Exception as e:
                    logger.error("Failed to create directory %s: %s", dir_str, str(e))
                    self._console.print(
                        f"[red bold]Error:[/red bold] Failed to create directory {dir_str}. "
                        "Please try again."
                    )
                    continue

    def export_tables_to_dir(self, target_dir: Path) -> None:
        """Export database tables to CSV files in the target directory.

        Args:
            target_dir (Path): Target directory for CSV export.
        """
        export_summary = self._exporter.export_tables_to_dir(target_dir)
        for table_name, csv_path, n_records in export_summary:
            self._console.print(
                f"[green]Exported[/green] {n_records} '[bold]{table_name}[/bold]' "
                f"[green]records to[/green] [bold]{csv_path}[/bold]"
            )


def main() -> None:
    from dotenv import load_dotenv

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.composition import (
        Lifetime,
        build_base_sqlite_uow_container,
    )
    from nwtrack.bootstrap.logging_config import setup_logging

    load_dotenv()
    setup_logging()

    container = build_base_sqlite_uow_container()
    container.register(
        Console,
        lambda c: Console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        ExportCSV,
        lambda c: ExportCSV(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        ExportTablesCSVDir,
        lambda c: ExportTablesCSVDir(
            exporter=c.resolve(ExportCSV), console=c.resolve(Console)
        ),
    )
    container.resolve(ExportTablesCSVDir).run()


if __name__ == "__main__":
    main()
