"""
CLI application using Typer to access use cases and services.
"""

import os
from pathlib import Path

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
import_app = typer.Typer(help="Import commands", no_args_is_help=True)
admin_app = typer.Typer(help="Admin commands", no_args_is_help=True)
tui_app = typer.Typer(help="TUI commands", no_args_is_help=True)
config_app = typer.Typer(help="Config commands", no_args_is_help=True)

app.add_typer(accounts_app, name="accounts")
app.add_typer(balances_app, name="balances")
app.add_typer(categories_app, name="categories")
app.add_typer(institutions_app, name="institutions")
app.add_typer(tags_app, name="tags")
app.add_typer(reports_app, name="reports")
app.add_typer(export_app, name="export")
app.add_typer(import_app, name="import")
app.add_typer(admin_app, name="admin")
app.add_typer(tui_app, name="tui")
app.add_typer(config_app, name="config")


def _ensure_runtime_schema() -> None:
    from nwtrack.application.services.db_admin import DBAdminService
    from nwtrack.bootstrap.composition import (
        build_base_container,
        build_data_services_container,
    )

    container = build_data_services_container(build_base_container())
    container.resolve(DBAdminService).ensure_database()


def _record_config_file_override(config_file: Path | None) -> None:
    """Publish the explicit config file path (flag, else env var) for settings
    resolution, or clear it when neither is given."""
    from nwtrack.infra.config.paths import (
        ConfigFileOverride,
        ConfigFileOverrideSource,
        set_config_file_override,
    )

    if config_file is not None:
        override = ConfigFileOverride(
            config_file.expanduser().resolve(), ConfigFileOverrideSource.FLAG
        )
    elif env_value := os.environ.get(ConfigFileOverrideSource.ENV.value):
        override = ConfigFileOverride(
            Path(env_value).expanduser().resolve(), ConfigFileOverrideSource.ENV
        )
    else:
        override = None
    set_config_file_override(override)


@app.callback()
def main(
    ctx: typer.Context,
    config_file: Path | None = typer.Option(
        None,
        "--config-file",
        help=(
            "Use this config.toml instead of searching the standard locations "
            "(overrides NWTRACK_CONFIG_FILE)."
        ),
    ),
) -> None:
    """Ensure the runtime database schema before executing a command."""
    _record_config_file_override(config_file)
    # Config commands never touch the database, and `config init` must be able to
    # create the file a missing --config-file points at.
    if ctx.invoked_subcommand is None or ctx.invoked_subcommand == "config":
        return
    _ensure_runtime_schema()


# import command modules so decorators register commands
from nwtrack.entrypoints.cli.commands import (  # noqa: F401, E402
    accounts,
    admin,
    balances,
    categories,
    config,
    export,
    imports,
    institutions,
    reports,
    tags,
    tui,
)
