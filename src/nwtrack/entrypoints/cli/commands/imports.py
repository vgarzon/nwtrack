"""
Import commands.
"""

import logging

from rich.console import Console

from nwtrack.bootstrap.container import Container
from nwtrack.entrypoints.cli.app import import_app

logger = logging.getLogger(__name__)


@import_app.command("tables-csv")
def main(
    source_dir: str = "",
    interactive: bool = False,
):
    """Import database tables from CSV files in the specified directory."""
    from nwtrack.application.use_cases.import_tables_csv import (
        bootstrap,
        run_cli,
        run_interactive,
    )

    container: Container = bootstrap()
    console: Console = container.resolve(Console)

    if interactive:
        console.print("[bold]Running import in interactive mode...[/bold]")
        defaults = {"source_dir": source_dir}
        run_interactive(container, defaults)
    else:
        console.print("[bold]Running import in CLI mode...[/bold]")
        run_cli(container, source_dir)
