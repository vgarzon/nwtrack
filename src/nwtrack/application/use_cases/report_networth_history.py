"""
Print networth history report.
"""

import logging

from rich.console import Console
from rich.table import Table

from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import NetWorth

logger = logging.getLogger(__name__)


class NetworthHistoryReport:
    """Print networth history report."""

    def __init__(self, fetcher: FetchService, console: Console) -> None:
        self._fetcher = fetcher
        self._console = console

    def run(self, n_months: int = 12) -> None:
        """Run the summary service.

        Args:
            n_months (int): Number of months to include in the report, defaults to 12
        """
        logger.info("Starting Networth History Report Service")
        self._console.rule("[bold green]Networth History Report", align="center")
        # NOTE: Variable currency_code is currently hardcoded to "USD"
        self.print_net_worth_history(n_months, "USD")
        logger.info("Finished Networth History Report Service")

    def print_net_worth_history(self, n: int = 12, currency_code: str = "USD") -> None:
        """Print net worth on a specific month.

        Args:
            n: Number of months to retrieve, defaults to 12
            currency (str): Currency code (default: "USD")

        Returns:
            None
        """
        nws = self._fetcher.get_last_n_networth(n, currency_code)
        if not nws:
            logger.warning("No net worth history found in %s", currency_code)
            self._console.print(
                f"[red]No net worth data found in {currency_code}[/red]"
            )
            return
        if len(nws) < n:
            logger.warning(
                "Requested %d months of net worth history, but only %d found.",
                n,
                len(nws),
            )
            self._console.print(
                f"[yellow]Only {len(nws)} months of net worth data found in "
                f"{currency_code}[/yellow]"
            )
        nws.sort(key=lambda x: x.month)  # Ensure chronological order
        table = self._build_networth_history_table(nws)
        self._console.print(table)

    def _build_networth_history_table(self, nws: list[NetWorth]) -> Table:
        """Build a Rich Table of net worth summary.

        Args:
            nws (list[NetWorth]): List of Net Worth records

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


def main(n_months: int = 12) -> None:
    """Main entry point for networth history report script.

    Args:
        n_months (int): Number of months to include in the report, defaults to 12
    """
    from dotenv import load_dotenv

    from nwtrack.application.ports.uow import UnitOfWork
    from nwtrack.bootstrap.composition import Lifetime, build_base_sqlite_uow_container
    from nwtrack.bootstrap.logging_config import setup_logging

    load_dotenv()
    setup_logging()

    container = build_base_sqlite_uow_container()
    container.register(
        Console,
        lambda c: Console(),
        lifetime=Lifetime.SINGLETON,
    ).register(
        FetchService,
        lambda c: FetchService(uow=lambda: c.resolve(UnitOfWork)),
    ).register(
        NetworthHistoryReport,
        lambda c: NetworthHistoryReport(
            fetcher=c.resolve(FetchService),
            console=c.resolve(Console),
        ),
    )
    service: NetworthHistoryReport = container.resolve(NetworthHistoryReport)
    service.run(n_months)


if __name__ == "__main__":
    import sys

    if sys.argv[1:]:
        n_months = int(sys.argv[1])
    else:
        n_months = 12

    main(n_months)
