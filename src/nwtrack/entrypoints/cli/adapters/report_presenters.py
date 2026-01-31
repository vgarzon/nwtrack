"""
Rich-based presenters for report-related use cases.
"""

from rich.console import Console
from rich.table import Table

from nwtrack.domain.models import NetWorth


class RichNetworthHistoryPresenter:
    """Rich-based implementation of NetworthHistoryPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def show_header(self) -> None:
        """Display report header using Rich."""
        self._console.rule("[bold green]Networth History Report", align="center")

    def display_networth_history(
        self, networth_records: list[NetWorth], currency_code: str
    ) -> None:
        """Display networth history table using Rich.

        Args:
            networth_records: List of networth records to display
            currency_code: Currency code for the report
        """
        table = self._build_networth_history_table(networth_records)
        self._console.print(table)

    def show_no_data_warning(self, currency_code: str) -> None:
        """Display warning when no data is found.

        Args:
            currency_code: Currency code that was searched
        """
        self._console.print(f"[red]No net worth data found in {currency_code}[/red]")

    def show_partial_data_warning(
        self, requested: int, found: int, currency_code: str
    ) -> None:
        """Display warning when fewer records than requested are found.

        Args:
            requested: Number of months requested
            found: Number of months actually found
            currency_code: Currency code for the report
        """
        self._console.print(
            f"[yellow]Only {found} months of net worth data found in "
            f"{currency_code}[/yellow]"
        )

    def _build_networth_history_table(self, nws: list[NetWorth]) -> Table:
        """Build a Rich Table of net worth summary.

        Args:
            nws: List of Net Worth records

        Returns:
            Table: Rich Table object
        """
        _first_month = nws[0].month if nws else ""
        _last_month = nws[-1].month if nws else ""
        _title = f"Net Worth History {_first_month} to {_last_month}"
        table = Table(title=f"[green]{_title}[/green]")
        table.add_column("Month", justify="right")
        table.add_column("Assets", justify="right", style="green")
        table.add_column("Liabilities", justify="right", style="yellow")
        table.add_column("Net Worth", justify="right", style="red")
        table.add_column("Change", justify="right")
        for k, nw in enumerate(nws):
            if k > 0:
                change = nw.net_worth - nws[k - 1].net_worth
                color_str = "red" if change < 0 else "green"
                change_str = f"[{color_str}]{change:7,}[/{color_str}]"
            else:
                change_str = ""
            table.add_row(
                f"{nw.month}",
                f"{nw.assets:9,}",
                f"{nw.liabilities:9,}",
                f"{nw.net_worth:9,}",
                f"{change_str}",
            )
        return table
