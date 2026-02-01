"""
Database administrator presenters
"""

from rich.console import Console
from rich.prompt import Confirm, Prompt

from nwtrack.entrypoints.cli.ui.renderers import build_file_paths_table


class RichDBInitCSVPresenter:
    """Rich-based implementation of DBInitCSVPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console
        self._prompt = Prompt(console=self._console)
        self._confirm = Confirm(console=self._console)

    def show_header(self, db_file_path: str, db_ddl_path: str) -> None:
        """Display workflow header using Rich.

        Args:
            db_file_path: Path to the SQLite database file
            db_ddl_path: Path to the DDL script file
        """
        self._console.rule("[bold green]Initialize DB from CSV Files[/bold green]")
        self._console.print(
            f"[bold]SQLite db file path:[/bold] {db_file_path}\n"
            f"[bold]DDL script path:[/bold] {db_ddl_path}"
        )

    def prompt_for_file_paths(self, table_names: list[str]) -> dict[str, str]:
        """Prompt user to input CSV file paths for required tables.

        Args:
            table_names: List of required table names

        Returns:
            Dictionary of table names to file paths
        """
        from pathlib import Path

        file_paths = {}
        self._console.print(
            "[yellow]Please enter CSV file paths or 'q' to quit:[/yellow]"
        )
        for table_name in table_names:
            while True:
                path_str = self._prompt.ask(f"[bold]{table_name}[/bold]").strip()
                if path_str.lower() == "q":
                    raise KeyboardInterrupt
                if not Path(path_str).is_file():
                    self._console.print(
                        f"[red bold]Error: File not found[/red bold]: {path_str}. "
                        "Please try again."
                    )
                    continue
                else:
                    file_paths[table_name] = path_str
                    break
        return file_paths

    def show_file_paths_table(self, file_paths: dict[str, str]) -> None:
        """Display the table of file paths.

        Args:
            file_paths (dict[str, str]: Dictionary of table names to file paths
        """
        table = build_file_paths_table(file_paths, title_prefix="Specified CSV")
        self._console.print(table)

    def prompt_for_confirmation(self) -> bool:
        """Prompt user to confirm continuation.

        Returns:
            True if user confirms, False otherwise
        """
        self._console.print(
            "\n[bold orange3]WARNING:[/bold orange3] This script will "
            "[bold]DELETE and RE-CREATE[/bold] the database.\n"
        )
        return self._confirm.ask("Do you want to continue?", default=False)

    def show_cancellation(self) -> None:
        """Display user cancellation message."""
        self._console.print("[orange]Database initialization aborted by user.[/orange]")

    def show_success(self) -> None:
        """Display successful completion message."""
        self._console.print("[green]Database initialized successfully.[/green]")

    def show_error(self, message: str) -> None:
        """Display error message.

        Args:
            message: Error message string
        """
        self._console.print(f"[red bold]Error:[/red bold] {message}")
