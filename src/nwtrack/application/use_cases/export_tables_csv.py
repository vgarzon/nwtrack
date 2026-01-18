"""
Export tables to csv files.
"""

import logging
from typing import Callable
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.infra.fileio.csv_io import records_to_csv

logger = logging.getLogger(__name__)


class ExportTablesCSV:
    """Export database tables to CSV files."""

    def __init__(self, uow: Callable[[], UnitOfWork], console: Console) -> None:
        self._uow = uow
        self._console = console
        # TODO: Use RepoRegistry to specify table names
        self._table_names = [
            "currencies",
            "categories",
            "accounts",
            "balances",
            "exchange_rates",
        ]

    def run(self) -> None:
        """Run the export process."""
        logger.info("Starting Export Tables to CSV files.")
        self._console.rule("[bold green]Export Tables to CSV[/bold green]")
        target_dir = self.collect_target_dir()
        self.export_tables_to_csv(target_dir)
        logger.info("Finished exporting tables to CSV files.")

    def collect_target_dir(self) -> Path:
        """Collect and validate target directory from user input.

        Returns:
            target_dir (Path): Validated target directory path.
        Exceptions:
            KeyboardInterrupt: if user interrupts input
        """
        while True:
            dir_str = Prompt.ask(
                "[yellow]Please enter target directory for CSV export or 'q' to quit[/yellow]"
            ).strip()
            if dir_str.lower() == "q":
                logger.warning("User aborted csv export target directory input")
                raise KeyboardInterrupt
            target_dir = Path(dir_str)
            if not target_dir.is_dir():
                self._console.print(
                    f"[red bold]Error: Directory not found[/red bold]: {dir_str}. "
                    "Please try again."
                )
                continue
            else:
                return target_dir

    def export_tables_to_csv(self, target_dir: Path) -> None:
        """Export database tables to CSV files in the target directory.

        Args:
            target_dir (Path): Target directory for CSV export.
        """
        for table_name in self._table_names:
            csv_path = target_dir / f"{table_name}.csv"
            with self._uow() as uow:
                try:
                    repo = getattr(uow, table_name)
                except AttributeError:
                    logger.error(
                        "Repository for table %s not found. Skipping.", table_name
                    )
                    continue
                entities = repo.get_all()
                records = [repo._mapper.to_record(entity) for entity in entities]

            if not records:
                logger.info(
                    "No records found in table %s. Skipping export.", table_name
                )
                continue

            records_to_csv(records, csv_path)
            logger.info("Exported table %s to %s", table_name, csv_path)
            self._console.print(
                f"[green]Exported[/green] {len(records)} [bold]{table_name}[/bold] "
                f"[green]to[/green] [bold]{csv_path}[/bold]"
            )


def main() -> None:
    from dotenv import load_dotenv

    from nwtrack.bootstrap.composition import (
        build_base_sqlite_uow_container,
        Lifetime,
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
        ExportTablesCSV,
        lambda c: ExportTablesCSV(
            uow=lambda: c.resolve(UnitOfWork), console=c.resolve(Console)
        ),
    )
    container.resolve(ExportTablesCSV).run()


if __name__ == "__main__":
    main()
