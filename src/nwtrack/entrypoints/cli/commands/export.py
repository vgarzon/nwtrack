"""
Export commands
"""

import logging

from nwtrack.bootstrap.container import Container
from nwtrack.entrypoints.cli.app import export_app

logger = logging.getLogger(__name__)


@export_app.command("tables-csv")
def main(
    interactive: bool = False,
    target_dir: str = "",
    create: bool = False,
):
    """Export database tables to CSV files in the specified directory.

    Args:
        interactive (bool): Whether to run in interactive mode.
        target_dir (str): Target directory for CSV export.
        create (bool): Whether to create the directory if it does not exist.
    """
    from nwtrack.application.use_cases.export_tables_csv import (
        bootstrap,
        run_cli,
        run_interactive,
    )

    container: Container = bootstrap()

    if interactive:
        defaults = {"target_dir": target_dir, "create": create}
        run_interactive(container, defaults)
    else:
        run_cli(container, target_dir, create)
