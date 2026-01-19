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


def export_tables_to_csv(container: Container, target_path: Path):
    """
    Export database tables to CSV files in the specified directory.
    """
    _table_names = [
        "currencies",
        "categories",
        "accounts",
        "balances",
        "exchange_rates",
    ]
    console = container.resolve(Console)
    exporter = container.resolve(ExportCSV)
    for table_name in _table_names:
        csv_path = target_path / f"{table_name}.csv"
        n_records = exporter.export_table(table_name, csv_path)
        console.print(
            f"[green]Exported[/green] {n_records} [bold]{table_name}[/bold] "
            f"[green]to[/green] [bold]{csv_path}[/bold]"
        )


@export_app.command("tables-csv")
def main(target_dir: str, create: bool = False):
    """Export database tables to CSV files in the specified directory.

    Args:
        target_dir (str): Target directory for CSV export.
        create (bool): Whether to create the directory if it does not exist.
    """
    container = bootstrap()
    console: Console = container.resolve(Console)
    target_path = Path(target_dir)
    if target_path.exists() and not target_path.is_dir():
        logger.error("Target path %s is not a directory.", target_path)
        console.print(
            f"[red]Error:[/red] Target path {target_path} is not a directory."
        )
        exit(1)
    if not target_path.exists() and not create:
        logger.error("Target directory %s does not exist.", target_path)
        console.print(
            f"[red]Error:[/red] Target directory {target_path} does not exist. "
            "Use --create to create it."
        )
        exit(1)
    if not target_path.is_dir():
        logger.info("Creating directory %s.", target_path)
        console.print(f"[yellow]Creating directory[/yellow]: {target_path}")
        target_path.mkdir(parents=True, exist_ok=True)
    export_tables_to_csv(container, target_path)
