"""
Export tables to csv files.
"""

import logging
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt

from nwtrack.application.services.export_csv import ExportCSV
from nwtrack.bootstrap.container import Container

logger = logging.getLogger(__name__)


class ExportTablesCSVBase:
    """Base class for exporting database tables to CSV files."""

    def __init__(self, exporter: ExportCSV, console: Console) -> None:
        self._exporter = exporter
        self._console = console

    def create_target_path(self, target_path: Path) -> bool:
        """Create the target directory for CSV export.

        Args:
            target_path (Path): Target directory path.

        Returns:
            bool: Success flag.
        """
        logger.info("Creating directory %s.", target_path)
        self._console.print(f"[yellow]Creating directory[/yellow]: {target_path}")
        try:
            target_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("Failed to create directory %s: %s", target_path, str(e))
            self._console.print(
                f"[red bold]Error:[/red bold] Failed to create directory "
                f"{target_path}. Aborting export."
            )
            return False
        return True

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


class ExportTablesCSVInteractive(ExportTablesCSVBase):
    """Export database tables to CSV files."""

    def __init__(self, exporter: ExportCSV, console: Console) -> None:
        super().__init__(exporter, console)
        self._prompt = Prompt(console=self._console)
        self._confirm = Confirm(console=self._console)

    def run(self, defaults: dict) -> None:
        """Run the export process."""
        logger.info("Starting Export Tables to CSV files.")
        self._console.rule("[bold green]Export Tables to CSV[/bold green]")
        try:
            target_dir = self.collect_target_dir(defaults=defaults)
        except KeyboardInterrupt:
            self._console.print("[red]CSV export aborted by user.[/red]")
            return
        self.export_tables_to_dir(target_dir)
        logger.info("Finished exporting tables to CSV files.")

    def collect_target_dir(self, defaults: dict) -> Path:
        """Collect and validate target directory from user input.

        Args:
            defaults (dict): Default parameters for interactive prompts.

        Returns:
            target_dir (Path): Validated target directory path.

        Exceptions:
            KeyboardInterrupt: if user interrupts input
        """
        while True:
            target_dir = self._prompt.ask(
                "[yellow]Please enter target directory or 'q' to quit[/yellow]",
                default=defaults.get("target_dir", ""),
            ).strip()
            if target_dir.lower() == "q":
                logger.warning("User aborted csv export target directory input")
                raise KeyboardInterrupt
            target_path = Path(target_dir)
            if target_path.is_dir():
                return target_path

            create = self._confirm.ask(
                f"[red]Directory [/red][bold]{target_dir}[/bold] "
                "[red]does not exist. Create it?[/red]",
                default=defaults.get("create", False),
            )
            if create:
                success = self.create_target_path(target_path)
                if success:
                    return target_path


class ExportTablesCSVCLI(ExportTablesCSVBase):
    """Export database tables to CSV files via CLI."""

    def __init__(self, exporter: ExportCSV, console: Console) -> None:
        super().__init__(exporter, console)
        self._exporter = exporter
        self._console = console

    def run(self, target_dir: str, create: bool = False) -> None:
        """Run the export process.

        Args:
            target_dir (str): Target directory for CSV export.
            create (bool): Whether to create the directory if it does not exist.
        """
        logger.info("Starting Export Tables to CSV files.")
        self._console.rule("[bold green]Export Tables to CSV[/bold green]")
        target_path, valid = self.check_or_create_target_dir(target_dir, create)
        if not valid:
            logger.error("Invalid target directory %s. Aborting export.", target_dir)
            return
        self.export_tables_to_dir(target_path)
        logger.info("Finished exporting tables to CSV files.")

    def check_or_create_target_dir(
        self, target_dir: str, create: bool
    ) -> tuple[Path, bool]:
        """Check or create the target directory for CSV export.

        Args:
            target_dir (str): Target directory path.
            create (bool): Whether to create the directory if it does not exist.

        Returns:
            tuple[Path, bool]: Validated target directory path and success flag.
        """
        target_path = Path(target_dir)
        if target_path.exists() and not target_path.is_dir():
            logger.error("Target path %s is not a directory.", target_path)
            self._console.print(
                f"[red]Error:[/red] Target path {target_path} is not a directory."
            )
            return target_path, False
        if not target_path.exists() and not create:
            logger.error("Target directory %s does not exist.", target_path)
            self._console.print(
                f"[red]Error:[/red] Target directory {target_path} does not exist. "
                "Use --create to create it."
            )
            return target_path, False
        success = self.create_target_path(target_path)
        return target_path, success


def bootstrap() -> Container:
    from dotenv import load_dotenv

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.composition import build_base_sqlite_uow_container
    from nwtrack.bootstrap.logging_config import setup_logging

    load_dotenv()
    setup_logging()
    container = build_base_sqlite_uow_container()
    container.register(
        Console,
        lambda c: Console(),
    ).register(
        ExportCSV,
        lambda c: ExportCSV(uow=lambda: c.resolve(UnitOfWork)),
    )
    return container


def run_interactive(container: Container, defaults: dict) -> None:
    """Run export in interactive mode.
    Args:
        container (Container): Dependency injection container.
        defaults (dict): Default parameters for interactive prompts.
    """
    container.register(
        ExportTablesCSVInteractive,
        lambda c: ExportTablesCSVInteractive(
            exporter=c.resolve(ExportCSV), console=c.resolve(Console)
        ),
    )
    container.resolve(ExportTablesCSVInteractive).run(defaults)


def run_cli(container: Container, target_dir: str, create: bool) -> None:
    """Run export in CLI mode.
    Args:
        target_dir (str): Target directory for CSV export.
        create (bool): Whether to create the directory if it does not exist.
    """
    container.register(
        ExportTablesCSVCLI,
        lambda c: ExportTablesCSVCLI(
            exporter=c.resolve(ExportCSV), console=c.resolve(Console)
        ),
    )
    container.resolve(ExportTablesCSVCLI).run(target_dir=target_dir, create=create)


if __name__ == "__main__":
    import sys

    container: Container = bootstrap()
    console: Console = container.resolve(Console)

    argv = sys.argv[1:]
    if not argv:
        console.print(
            "[yellow]No command line arguments provided. "
            "Running in interactive mode.[/yellow]"
        )
        mode = "interactive"
    else:
        mode = "cli"
        target_dir = argv[0]
        create_flag = "--create" in argv
        console.print(
            f"[yellow]Running in CLI mode. Target directory: {target_dir} "
            f"Create flag: {create_flag}[/yellow]"
        )

    if mode == "interactive":
        run_interactive(container, defaults={})
    else:
        run_cli(container, target_dir=target_dir, create=create_flag)
