"""
Database initializer services
"""

import logging
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

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
    ) -> None:
        self._config = config
        self._admin_svc = admin_svc
        self._data_svc = data_svc
        # TODO: Use RepoRegistry to specify required keys
        self._required_keys = [
            "currencies",
            "categories",
            "accounts",
            "balances",
            "exchange_rates",
        ]
        self._file_paths: dict[str, str] = {}
        self._console = Console()

    def run(self) -> None:
        """Run the database initialization process."""
        logger.info("Starting database initialization from CSV files.")
        logger.info("Database file path: %s", self._config.db_file_path)
        logger.info("DDL script path: %s", self._config.db_ddl_path)
        self._console.rule(
            "[bold green]Database Initialization from CSV Files[/bold green]"
        )
        self._console.print(
            f"[bold]SQLite db file path:[/bold] {self._config.db_file_path}\n"
            f"[bold]DDL script path:[/bold] {self._config.db_ddl_path}"
        )
        try:
            self.collect_file_paths()
        except KeyboardInterrupt:
            logging.warnmng("User aborted csv file input.")
            self._console.print("[orange]Stopping.[/orange]")
            return
        fp_table = self._build_file_paths_table()
        self._console.print(fp_table)
        self._console.print(
            "\n[bold orange3]WARNING:[/bold orange3] This script will "
            "[bold]DELETE and RE-CREATE[/bold] the database.\n"
        )
        accept = Confirm.ask("Do you want to continue?", default=False)
        if not accept:
            logger.warning("User aborted database initialization.")
            self._console.print("[orange]Stopping.[/orange]")
            return

        self._console.print("[yellow]Initializing SQLite database.[/yellow]")
        self._admin_svc.init_database()
        self._data_svc.insert_data_from_csv(self._file_paths)
        self._console.print("[green]Database initialized successfully.[/green]")
        logger.info("Finished database initialization from CSV files.")

    def _build_file_paths_table(self) -> Table:
        """Build a table of file paths for display.

        Returns:
            Table: Rich Table object with file paths
        """
        table = Table(title="Specified CSV File Paths")
        table.add_column("Repo", style="cyan", no_wrap=True)
        table.add_column("Path", style="magenta")
        for key, path in self._file_paths.items():
            table.add_row(key, path)
        return table

    def collect_file_paths(self) -> None:
        """Collect and validate file pahhs from user input.

        Returns:
            None

        Exceptions:
            KeyboardInterrupt: if user interrupts input
        """
        file_paths = {}
        self._console.print(
            "[yellow]Please enter CSV file paths or 'q' to quit:[/yellow]"
        )
        for file_key in self._required_keys:
            while True:
                path_str = Prompt.ask(f"[bold]{file_key}[/bold]").strip()
                if path_str.lower() == "q":
                    logger.warning("User aborted csv file input for key %s", file_key)
                    raise KeyboardInterrupt
                path = Path(path_str)
                if not path.is_file():
                    self._console.print(
                        f"[red bold]Error: File not found[/red bold]: {path_str}. "
                        "Please try again."
                    )
                    continue
                else:
                    file_paths[file_key] = path_str
                    break
        self._file_paths = file_paths.copy()


def main() -> None:
    from dotenv import load_dotenv

    from nwtrack.application.ports.db import DBConnectionManager
    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.bootstrap.composition import (
        build_base_sqlite_uow_container,
    )
    from nwtrack.bootstrap.logging_config import setup_logging

    load_dotenv()
    setup_logging()

    container = build_base_sqlite_uow_container()
    container.register(
        DBAdminService,
        lambda c: DBAdminService(c.resolve(Settings), c.resolve(DBConnectionManager)),
    ).register(
        InitDataService,
        lambda c: InitDataService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        DBInitializerCSV,
        lambda c: DBInitializerCSV(
            c.resolve(Settings), c.resolve(DBAdminService), c.resolve(InitDataService)
        ),
    )
    db_initializer: DBInitializerCSV = container.resolve(DBInitializerCSV)
    db_initializer.run()


if __name__ == "__main__":
    main()
