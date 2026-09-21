"""CLI config commands."""

from nwtrack.entrypoints.cli.app import config_app


@config_app.command("init")
def init() -> None:
    """Write a default config.toml to the standard config location."""
    import nwtrack.application.use_cases.init_config as uc

    uc.main()


@config_app.command("show")
def show() -> None:
    """Show the active config.toml, search-path priority, and resolved settings."""
    import nwtrack.application.use_cases.show_config as uc

    uc.main()
