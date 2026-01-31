"""
Rich console factory to be used in DI containers.
"""

from rich.console import Console

from nwtrack.entrypoints.cli.ui.console import ConsoleSettings, build_console


class ConsoleFactory:
    """Factory class to create Rich console instances."""

    def __init__(self, default_settings: ConsoleSettings | None = None) -> None:
        self._default = default_settings or ConsoleSettings()

    def __call__(self, *, record: bool | None = None) -> Console:
        """Create and return a Rich console instance.

        Args:
            record (bool | None): If provided, overrides the record setting in
                ConsoleSettings.

        Returns:
            Console: Configured Rich console instance.
        """
        settings = ConsoleSettings(
            theme=self._default.theme,
            width=self._default.width,
            record=record if record is not None else self._default.record,
        )
        return build_console(settings)
