"""
CSV import and export presenter adapters.
"""

from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt


class RichImportTablesCSVPresenter:
    """Rich-based implementation of ImportTablesCSVPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console
        self._prompt = Prompt(console=self._console)

    def show_header(self) -> None:
        self._console.rule("[header]Import Tables from CSV[/header]")

    def prompt_for_source_dir(self, default: str) -> str:
        return self._prompt.ask(
            "[label]Please enter source directory or 'q' to quit[/label]",
            default=default,
        ).strip()

    def show_cancellation(self) -> None:
        self._console.print("[cancel]CSV import aborted by user.[/cancel]")

    def show_import_success(self, source_dir: Path) -> None:
        self._console.print(
            f"[success]Imported[/success] CSV tables from [bold]{source_dir}[/bold]"
        )

    def show_error(self, message: str) -> None:
        self._console.print(f"[error]Error:[/error] {message}")


class RichExportTablesCSVPresenter:
    """Rich-based implementation of ExportTablesCSVPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console
        self._prompt = Prompt(console=self._console)
        self._confirm = Confirm(console=self._console)

    def show_header(self) -> None:
        self._console.rule("[header]Export Tables to CSV[/header]")

    def prompt_for_target_dir(self, default: str) -> str:
        return self._prompt.ask(
            "[label]Please enter target directory or 'q' to quit[/label]",
            default=default,
        ).strip()

    def confirm_create_directory(self, target_dir: str) -> bool:
        return self._confirm.ask(
            f"[warning]Directory[/warning] [bold]{target_dir}[/bold] "
            "[warning]does not exist. Create it?[/warning]",
            default=False,
        )

    def show_creating_directory(self, target_dir: Path) -> None:
        self._console.print(f"[label]Creating directory[/label]: {target_dir}")

    def show_directory_create_error(self, target_dir: Path, message: str) -> None:
        self._console.print(
            f"[error]Error:[/error] Failed to create directory "
            f"{target_dir}. Aborting export. {message}"
        )

    def show_directory_not_found_error(self, target_dir: Path) -> None:
        self._console.print(
            f"[error]Error:[/error] Target directory {target_dir} does not exist. "
            "Use --create to create it."
        )

    def show_not_a_directory_error(self, target_dir: Path) -> None:
        self._console.print(
            f"[error]Error:[/error] Target path {target_dir} is not a directory."
        )

    def show_cancellation(self) -> None:
        self._console.print("[cancel]CSV export aborted by user.[/cancel]")

    def show_table_exported(
        self, table_name: str, csv_path: Path, n_records: int
    ) -> None:
        self._console.print(
            f"[success]Exported[/success] {n_records} '[bold]{table_name}[/bold]' "
            f"[success]records to[/success] [bold]{csv_path}[/bold]"
        )

    def show_table_skipped(self, table_name: str) -> None:
        self._console.print(
            f"[info]Skipped empty[/info] '[bold]{table_name}[/bold]' table."
        )
