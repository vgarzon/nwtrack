"""
CLI application using Typer to access use cases and services.
"""

import typer

app = typer.Typer(
    name="nwtrack",
    help="nwtrack - net worth tracker",
    add_completion=False,
    no_args_is_help=True,
)

accounts_app = typer.Typer(help="Account commands", no_args_is_help=True)
balances_app = typer.Typer(help="Balance commands", no_args_is_help=True)
categories_app = typer.Typer(help="Categories commands", no_args_is_help=True)
institutions_app = typer.Typer(help="Institution commands", no_args_is_help=True)
tags_app = typer.Typer(help="Tag commands", no_args_is_help=True)
reports_app = typer.Typer(help="Report commands", no_args_is_help=True)
export_app = typer.Typer(help="Export commands", no_args_is_help=True)

app.add_typer(accounts_app, name="accounts")
app.add_typer(balances_app, name="balances")
app.add_typer(categories_app, name="categories")
app.add_typer(institutions_app, name="institutions")
app.add_typer(tags_app, name="tags")
app.add_typer(reports_app, name="reports")
app.add_typer(export_app, name="export")


def _ensure_runtime_schema() -> None:
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.bootstrap.composition import (
        build_base_container,
        build_data_services_container,
    )

    container = build_data_services_container(build_base_container())
    container.resolve(DBAdminService).ensure_database()


@app.callback()
def main(ctx: typer.Context) -> None:
    """Ensure the runtime database schema before executing a command."""
    if ctx.invoked_subcommand is None:
        return
    _ensure_runtime_schema()

# import command modules so decorators register commands
from nwtrack.entrypoints.cli.commands import (  # noqa: F401, E402
    accounts,
    balances,
    categories,
    export,
    institutions,
    reports,
    tags,
)
