"""
Rich-based presenters for report-related use cases.
"""

from rich.console import Console
from rich.prompt import IntPrompt, Prompt

from nwtrack.application.dto import (
    AccountStatusScope,
    AggregationDimension,
    HistoryAggregationResult,
    MonthlyCategoryBalance,
    SingleMonthAggregationResult,
)
from nwtrack.application.services.fetch import FetchService
from nwtrack.domain.models import Account, Balance, NetWorth
from nwtrack.domain.value_objects import Month
from nwtrack.entrypoints.cli.ui.renderers import (
    build_accounts_table,
    build_balances_table,
    build_category_summary_table,
    build_month_balances_table,
    build_history_aggregation_table,
    build_networth_history_table,
    build_networth_history_total_change_table,
    build_networth_table,
    build_single_month_aggregation_table,
)


class RichNetworthHistoryPresenter:
    """Rich-based implementation of NetworthHistoryPresenter."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def show_header(self) -> None:
        """Display report header using Rich."""
        self._console.rule("[header]Networth History Report[/header]", align="center")

    def display_networth_history(
        self, networth_records: list[NetWorth], currency_code: str
    ) -> None:
        """Display networth history table using Rich.

        Args:
            networth_records: List of networth records to display
            currency_code: Currency code for the report
        """
        table = build_networth_history_table(networth_records)
        self._console.print(table)

    def show_no_data_warning(self, currency_code: str) -> None:
        """Display warning when no data is found.

        Args:
            currency_code: Currency code that was searched
        """
        self._console.print(
            f"[error]No net worth data found in {currency_code}[/error]"
        )

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
            f"[warning]Only {found} months of net worth data found in "
            f"{currency_code}[/warning]"
        )

    def display_total_change(
        self, networth_records: list[NetWorth], currency_code: str
    ) -> None:
        """Display total change in net worth over the period.

        Args:
            networth_records: List of networth records
            currency_code: Currency code for the report
        """
        if len(networth_records) < 2:
            return

        def calc_change(xa, xb, attr):
            """Calculate absolute and percentage change in attribute."""
            a = getattr(xa, attr)
            b = getattr(xb, attr)
            return b - a, (b - a) / a if a != 0 else 0

        changes = {
            k: calc_change(networth_records[0], networth_records[-1], k)
            for k in ["assets", "liabilities", "net_worth"]
        }
        table = build_networth_history_total_change_table(changes)
        self._console.print(table)


class RichBalancesByCategoryPresenter:
    """Rich-based implementation of BalancesByCategoryPresenter."""

    def __init__(self, fetcher: FetchService, console: Console) -> None:
        self._fetcher = fetcher
        self._console = console
        self._prompt = Prompt(console=console)
        self._int_prompt = IntPrompt(console=console)

    def show_header(self) -> None:
        """Display report header using Rich."""
        self._console.rule(
            "[header]Balance Summary by Category[/header]", align="center"
        )

    def show_accounts_table(
        self,
        accounts: list[Account],
        title_prefix: str = "",
    ) -> None:
        """Show active accounts."""
        table = build_accounts_table(accounts, title_prefix)
        self._console.print(table)

    def show_balances_table(
        self,
        balances: list[Balance],
        title_suffix: str = "",
    ) -> None:
        """Show balances table with account and category information.

        Args:
            balances: List of balances
            title_suffix: Suffix for the table title

        Returns:
            None
        """
        table = build_balances_table(balances, title_suffix=title_suffix)
        self._console.print(table)

    def show_summary_by_category(
        self, monthly_balances: list[MonthlyCategoryBalance], title_suffix: str = ""
    ) -> None:
        """Print summary by category for a specific month.

        Args:
            monthly_balances: list[MonthlyCategoryBalance]
            title_suffix: Suffix for the table title
        """
        table = build_category_summary_table(
            monthly_balances, title_suffix=title_suffix
        )
        self._console.print(table)

    def show_networth_table(
        self, nw: NetWorth, title_suffix: str = "", form: str = "wide"
    ) -> None:
        """Print net worth on a specific month.

        Args:
            nw (NetWorth): NetWorth object
            title_suffix (str): Suffix for the table title
            form (str): Table form, either "wide" or "long"

        Returns:
            None
        """
        table = build_networth_table(nw, title_suffix, form=form)
        self._console.print(table)

    def prompt_for_month_choice(
        self, balance_counts: list[tuple[Month, int]]
    ) -> Month | None:
        """Present month selection with recent months or custom input.

        Args:
            balance_counts: List of (Month, count) tuples for recent months

        Returns:
            Selected Month or None if cancelled
        """
        recent_months = [month for month, _ in balance_counts]
        n_months = len(balance_counts)

        table = build_month_balances_table(balance_counts)
        self._console.print(table)
        self._console.print("Options:")
        self._console.print("  [bold]A.[/bold] Enter year and month")
        self._console.print("  [bold]Q.[/bold] Quit")

        choice = self._prompt.ask(
            "[bold]Enter choice[/bold]",
            choices=[str(i + 1) for i in range(n_months)] + ["A", "Q"],
            default="1",
            case_sensitive=False,
        )

        if choice.lower().strip() == "q":
            return None
        if choice.lower().strip() == "a":
            return self._input_custom_month()

        choice_idx = int(choice) - 1
        return recent_months[choice_idx]

    def _input_custom_month(self) -> Month | None:
        """Input a specific month from user."""
        from datetime import date

        today = date.today()
        _year = self._int_prompt.ask("Enter year as 'YYYY'", default=today.year)
        _month = self._int_prompt.ask("Enter month as 'MM'", default=today.month)

        try:
            month = Month(year=_year, month=_month)
        except ValueError:
            self.show_invalid_month_error()
            return None

        if not self._fetcher.check_month_in_balances(month):
            self.show_no_balances_warning(month)
            return None

        return month

    def show_invalid_month_error(self) -> None:
        """Display error for invalid month input."""
        self._console.print("[error]Invalid month format. Please use YYYY-MM.[/error]")

    def show_no_balances_warning(self, month: Month) -> None:
        """Display warning when no balances found for month.

        Args:
            month: The month that has no balances
        """
        self._console.print(f"[warning]No balance entries found in {month}.[/warning]")

    def show_no_month_selected_message(self) -> None:
        """Display messag3 when no month is selected."""
        self._console.print("[warning]No month selected. Exiting report.[/warning]")

    def show_no_networth_data_warning(self, month: Month, currency_code: str) -> None:
        """Display warning when no net worth data found for month and currency.

        Args:
            month: The month that has no net worth data
            currency_code: The currency code that was searched
        """
        self._console.print(
            f"[error]No net worth data found for {month} in {currency_code}[/error]"
        )


class RichSingleMonthAggregationReportPresenter:
    """Rich-based implementation of the aggregated single-month report presenter."""

    def __init__(self, fetcher: FetchService, console: Console) -> None:
        self._fetcher = fetcher
        self._console = console
        self._prompt = Prompt(console=console)

    def show_header(self) -> None:
        """Display report header using Rich."""
        self._console.rule(
            "[header]Grouped Balance Report[/header]",
            align="center",
        )

    def prompt_for_month_choice(
        self, balance_counts: list[tuple[Month, int]]
    ) -> Month | None:
        """Present month selection with recent months or custom input."""
        recent_months = [month for month, _ in balance_counts]
        n_months = len(balance_counts)
        default_choice = self._default_month_choice(balance_counts)

        table = build_month_balances_table(balance_counts)
        self._console.print(table)
        self._console.print("Options:")
        self._console.print("  [bold]A.[/bold] Enter year and month")
        self._console.print("  [bold]Q.[/bold] Quit")

        choice = self._prompt.ask(
            "[bold]Enter choice[/bold]",
            choices=[str(i + 1) for i in range(n_months)] + ["A", "Q"],
            default=default_choice,
            case_sensitive=False,
        )

        if choice.lower().strip() == "q":
            return None
        if choice.lower().strip() == "a":
            return self._input_custom_month()

        choice_idx = int(choice) - 1
        return recent_months[choice_idx]

    @staticmethod
    def _default_month_choice(balance_counts: list[tuple[Month, int]]) -> str:
        """Prefer the most complete recent month when choosing a default option."""
        if not balance_counts:
            return "1"
        best_index = max(
            range(len(balance_counts)),
            key=lambda index: balance_counts[index][1],
        )
        return str(best_index + 1)

    def _input_custom_month(self) -> Month | None:
        """Input a specific month from user."""
        from datetime import date

        today = date.today()
        int_prompt = IntPrompt(console=self._console)
        _year = int_prompt.ask("Enter year as 'YYYY'", default=today.year)
        _month = int_prompt.ask("Enter month as 'MM'", default=today.month)

        try:
            month = Month(year=_year, month=_month)
        except ValueError:
            self.show_error("Invalid month format. Please use YYYY-MM.")
            return None

        if not self._fetcher.check_month_in_balances(month):
            self.show_error(f"No balance entries found in {month}.")
            return None

        return month

    def prompt_for_dimension_choice(self) -> AggregationDimension | None:
        """Prompt for one supported aggregation dimension."""
        dimensions = list(AggregationDimension)
        self._console.print("Dimensions:")
        for index, dimension in enumerate(dimensions, start=1):
            self._console.print(f"  [bold]{index}.[/bold] {dimension.value}")
        self._console.print("  [bold]Q.[/bold] Quit")
        choice = self._prompt.ask(
            "[bold]Enter dimension choice[/bold]",
            choices=[str(index) for index in range(1, len(dimensions) + 1)] + ["Q"],
            default="1",
            case_sensitive=False,
        )
        if choice.lower().strip() == "q":
            return None
        return dimensions[int(choice) - 1]

    def prompt_for_currency_choice(self, currencies: list[str]) -> str | None:
        """Prompt for one currency when a filter is required."""
        self._console.print("Currencies:")
        for index, currency in enumerate(currencies, start=1):
            self._console.print(f"  [bold]{index}.[/bold] {currency}")
        self._console.print("  [bold]Q.[/bold] Quit")
        choice = self._prompt.ask(
            "[bold]Enter currency choice[/bold]",
            choices=[str(index) for index in range(1, len(currencies) + 1)] + ["Q"],
            default="1",
            case_sensitive=False,
        )
        if choice.lower().strip() == "q":
            return None
        return currencies[int(choice) - 1]

    def show_no_month_selected_message(self) -> None:
        """Display feedback when month selection is cancelled."""
        self._console.print("[warning]No month selected. Exiting report.[/warning]")

    def show_no_dimension_selected_message(self) -> None:
        """Display feedback when dimension selection is cancelled."""
        self._console.print("[warning]No dimension selected. Exiting report.[/warning]")

    def show_no_currency_selected_message(self) -> None:
        """Display feedback when currency selection is cancelled."""
        self._console.print("[warning]No currency selected. Exiting report.[/warning]")

    def show_no_data_message(
        self,
        month: Month,
        dimension: AggregationDimension,
        status_scope: AccountStatusScope,
        currency_code: str | None,
    ) -> None:
        """Display feedback for valid requests with no grouped results."""
        currency_message = f" in {currency_code}" if currency_code is not None else ""
        self._console.print(
            f"[warning]No grouped balances found for {month} by "
            f"{dimension.value}{currency_message}.[/warning]"
        )

    def display_aggregation_report(
        self,
        result: SingleMonthAggregationResult,
    ) -> None:
        """Display grouped balances for a successful aggregation request."""
        table = build_single_month_aggregation_table(result)
        self._console.print(table)

    def show_error(self, message: str) -> None:
        """Display an error message."""
        self._console.print(f"[error]{message}[/error]")


class RichHistoryAggregationReportPresenter:
    """Rich-based implementation of the aggregated history report presenter."""

    def __init__(self, fetcher: FetchService, console: Console) -> None:
        self._fetcher = fetcher
        self._console = console
        self._prompt = Prompt(console=console)

    def show_header(self) -> None:
        """Display report header using Rich."""
        self._console.rule(
            "[header]Grouped History Balance Report[/header]",
            align="center",
        )

    def prompt_for_month_choice(
        self, balance_counts: list[tuple[Month, int]]
    ) -> Month | None:
        """Present month selection with recent months or custom input."""
        recent_months = [month for month, _ in balance_counts]
        n_months = len(balance_counts)
        default_choice = self._default_month_choice(balance_counts)

        table = build_month_balances_table(balance_counts)
        self._console.print(table)
        self._console.print("Options:")
        self._console.print("  [bold]A.[/bold] Enter year and month")
        self._console.print("  [bold]Q.[/bold] Quit")

        choice = self._prompt.ask(
            "[bold]Enter choice[/bold]",
            choices=[str(i + 1) for i in range(n_months)] + ["A", "Q"],
            default=default_choice,
            case_sensitive=False,
        )

        if choice.lower().strip() == "q":
            return None
        if choice.lower().strip() == "a":
            return self._input_custom_month()

        choice_idx = int(choice) - 1
        return recent_months[choice_idx]

    @staticmethod
    def _default_month_choice(balance_counts: list[tuple[Month, int]]) -> str:
        """Prefer the most complete recent month when choosing a default option."""
        if not balance_counts:
            return "1"
        best_index = max(
            range(len(balance_counts)),
            key=lambda index: balance_counts[index][1],
        )
        return str(best_index + 1)

    def _input_custom_month(self) -> Month | None:
        """Input a specific month from user."""
        from datetime import date

        today = date.today()
        int_prompt = IntPrompt(console=self._console)
        _year = int_prompt.ask("Enter year as 'YYYY'", default=today.year)
        _month = int_prompt.ask("Enter month as 'MM'", default=today.month)

        try:
            month = Month(year=_year, month=_month)
        except ValueError:
            self.show_error("Invalid month format. Please use YYYY-MM.")
            return None

        if not self._fetcher.check_month_in_balances(month):
            self.show_error(f"No balance entries found in {month}.")
            return None

        return month

    def prompt_for_dimension_choice(self) -> AggregationDimension | None:
        """Prompt for one supported aggregation dimension."""
        dimensions = list(AggregationDimension)
        self._console.print("Dimensions:")
        for index, dimension in enumerate(dimensions, start=1):
            self._console.print(f"  [bold]{index}.[/bold] {dimension.value}")
        self._console.print("  [bold]Q.[/bold] Quit")
        choice = self._prompt.ask(
            "[bold]Enter dimension choice[/bold]",
            choices=[str(index) for index in range(1, len(dimensions) + 1)] + ["Q"],
            default="1",
            case_sensitive=False,
        )
        if choice.lower().strip() == "q":
            return None
        return dimensions[int(choice) - 1]

    def prompt_for_currency_choice(self, currencies: list[str]) -> str | None:
        """Prompt for one currency when a filter is required."""
        self._console.print("Currencies:")
        for index, currency in enumerate(currencies, start=1):
            self._console.print(f"  [bold]{index}.[/bold] {currency}")
        self._console.print("  [bold]Q.[/bold] Quit")
        choice = self._prompt.ask(
            "[bold]Enter currency choice[/bold]",
            choices=[str(index) for index in range(1, len(currencies) + 1)] + ["Q"],
            default="1",
            case_sensitive=False,
        )
        if choice.lower().strip() == "q":
            return None
        return currencies[int(choice) - 1]

    def show_no_start_month_selected_message(self) -> None:
        """Display feedback when start-month selection is cancelled."""
        self._console.print("[warning]No start month selected. Exiting report.[/warning]")

    def show_no_end_month_selected_message(self) -> None:
        """Display feedback when end-month selection is cancelled."""
        self._console.print("[warning]No end month selected. Exiting report.[/warning]")

    def show_no_dimension_selected_message(self) -> None:
        """Display feedback when dimension selection is cancelled."""
        self._console.print("[warning]No dimension selected. Exiting report.[/warning]")

    def show_no_currency_selected_message(self) -> None:
        """Display feedback when currency selection is cancelled."""
        self._console.print("[warning]No currency selected. Exiting report.[/warning]")

    def show_no_data_message(
        self,
        start_month: Month,
        end_month: Month,
        dimension: AggregationDimension,
        status_scope: AccountStatusScope,
        currency_code: str | None,
    ) -> None:
        """Display feedback for valid requests with no grouped results."""
        currency_message = f" in {currency_code}" if currency_code is not None else ""
        self._console.print(
            f"[warning]No grouped balances found from {start_month} to "
            f"{end_month} by {dimension.value}{currency_message}.[/warning]"
        )

    def display_history_aggregation_report(
        self,
        result: HistoryAggregationResult,
    ) -> None:
        """Display grouped balances for a successful history aggregation request."""
        table = build_history_aggregation_table(result)
        self._console.print(table)

    def show_error(self, message: str) -> None:
        """Display an error message."""
        self._console.print(f"[error]{message}[/error]")
