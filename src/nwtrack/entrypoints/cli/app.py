"""
CLI application using Typer to access use cases and services.
"""

import typer

app = typer.Typer(
    name="nwtrack",
    help="nwtrack - net worth tracker",
    add_completion=False,
)

accounts_app = typer.Typer(help="Account commands")
balances_app = typer.Typer(help="Balance commands")
reports_app = typer.Typer(help="Report commands")

app.add_typer(accounts_app, name="accounts")
app.add_typer(balances_app, name="balances")
app.add_typer(reports_app, name="reports")

# import command modules so decorators register commands
from nwtrack.entrypoints.cli.commands import (  # noqa: F401, E402
    accounts,
    balances,
    reports,
)
