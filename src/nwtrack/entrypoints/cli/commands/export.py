"""
Export commands
"""

import logging
from pathlib import Path

from rich.console import Console

from nwtrack.application.services.export_csv import ExportCSV
from nwtrack.bootstrap.container import Container
from nwtrack.entrypoints.cli.app import export_app

logger = logging.getLogger(__name__)


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


def validate_target_directory(
    container: Container, target_dir: str, create: bool
) -> tuple[Path, bool]:
    """Validate the target directory for CSV export.

    Args:
        container (Container): Dependency injection container.
        target_dir (str): Target directory path.
        create (bool): Whether to create the directory if it does not exist.

    Returns:
        tuple[Path, bool]: Validated target directory path and success flag.
    """
    console: Console = container.resolve(Console)
    target_path = Path(target_dir)
    if target_path.exists() and not target_path.is_dir():
        logger.error("Target path %s is not a directory.", target_path)
        console.print(
            f"[red]Error:[/red] Target path {target_path} is not a directory."
        )
        return target_path, False
    if not target_path.exists() and not create:
        logger.error("Target directory %s does not exist.", target_path)
        console.print(
            f"[red]Error:[/red] Target directory {target_path} does not exist. "
            "Use --create to create it."
        )
        return target_path, False
    if not target_path.is_dir():
        logger.info("Creating directory %s.", target_path)
        console.print(f"[yellow]Creating directory[/yellow]: {target_path}")
        target_path.mkdir(parents=True, exist_ok=True)
    return target_path, True


def export_tables_to_csv(container: Container, target_path: Path) -> None:
    """
    Export database tables to CSV files in the specified directory.
    """
    console = container.resolve(Console)
    exporter = container.resolve(ExportCSV)
    export_summary = exporter.export_tables_to_dir(target_path)
    for table_name, csv_path, n_records in export_summary:
        console.print(
            f"[green]Exported[/green] {n_records} '[bold]{table_name}[/bold]' "
            f"[green]records to[/green] [bold]{csv_path}[/bold]"
        )


@export_app.command("tables-csv")
def main(target_dir: str, create: bool = False):
    """Export database tables to CSV files in the specified directory.

    Args:
        target_dir (str): Target directory for CSV export.
        create (bool): Whether to create the directory if it does not exist.
    """
    logger.info("Starting export of tables to CSV in directory: %s", target_dir)
    container = bootstrap()
    console = container.resolve(Console)
    target_path, success = validate_target_directory(container, target_dir, create)
    if not success:
        logger.error("Export aborted due to invalid target directory.")
        console.print("[red]Export aborted due to errors.[/red]")
        exit(1)
    export_tables_to_csv(container, target_path)
    logger.info("Export completed successfully.")
