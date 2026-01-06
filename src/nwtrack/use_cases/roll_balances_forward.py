"""
Roll balances forward to next available month.
"""

from typing import Callable

from nwtrack.domain.models import Balance
from nwtrack.domain.value_objects import Month
from nwtrack.unitofwork import UnitOfWork


class RollBalancesUpdater:
    """Update account balances interactively."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow

    def run(self) -> None:
        self.print_recent_months()
        target_month = self._get_next_free_month()
        print("Next available (target) month:", target_month)
        ans = input("Press Enter to continue or 'q' to quit: ")
        if ans.lower().strip() == "q":
            print("Quitting")
            return
        source_month = self.select_month()
        if source_month is None:
            print("Quitting")
            return
        self._copy_monthly_balances(source_month, target_month)
        self.print_net_worth(target_month)

    def _get_next_free_month(self) -> Month:
        """Get the next month that does not have balances yet.

        Returns:
            Month: Next month without balances.
        """
        recent_months = self._get_sorted_recent_months()
        latest_month = recent_months[0]
        next_month = latest_month.increment()
        return next_month

    def _get_sorted_recent_months(self) -> list[Month]:
        """Get sorted recent months with balances.

        Returns:
            list[Month]: List of recent months in descending order.
        """
        balance_counts = self._get_balance_count_per_month()
        if not balance_counts:
            raise ValueError("No balances found in the system.")
        balance_counts.sort(key=lambda x: x[0], reverse=True)
        recent_months = [month for month, _ in balance_counts]
        return recent_months

    def _copy_monthly_balances(self, source_month: Month, target_month: Month) -> None:
        """Copy all active account balances from one month to the next.

        Args:
            source_month (Month): Month to copy balances from.
            target_month (Month): Month to copy balances to.
        """
        with self._uow() as uow:
            if not uow.balances.check_month(source_month):
                raise ValueError(f"No balances found for month {source_month}")
        print(f"Rolling balances forward from {source_month} to {target_month}.")
        with self._uow() as uow:
            row_count = uow.balances.copy_by_month(source_month, target_month)
            if row_count == 0:
                print("No balances were copied.  Rolling back.")
                uow.rollback()

    def print_recent_months(self, length: int = 3) -> None:
        balance_counts = self._get_balance_count_per_month()
        balance_counts.sort(key=lambda x: x[0], reverse=True)
        print("\nRecent month balance counts:")
        for month, count in balance_counts[:length]:
            print(f"{month}: {count} balances")
        print()

    def select_month(self) -> Month | None:
        balance_counts = self._get_balance_count_per_month()
        balance_counts.sort(key=lambda x: x[0], reverse=True)
        latest_month = balance_counts[0][0]
        while True:
            response = input(
                f"Select '{latest_month}' as source month? (Y/N or 'q' to quit): "
            )
            if response.lower().strip() == "q":
                return None
            if response.lower().strip() == "y":
                return latest_month
            elif response.lower().strip() == "n":
                return self.input_month()
            else:
                print("Invalid input. Please enter 'Y', 'N', or 'q'.")
                continue
        return None

    def input_month(self) -> Month | None:
        while True:
            response = input("Enter year and month as 'YYYY MM' or 'q' to quit: ")
            if response.lower().strip() == "q":
                return None
            try:
                _year, _month = map(int, response.split())
            except ValueError:
                print("Invalid input format. Please use 'YYYY MM'.")
                continue

            try:
                month = Month(year=_year, month=_month)

            except ValueError:
                print("Invalid month format. Please use YYYY-MM.")
                continue
            break
        return month

    def print_net_worth(self, month: Month, currency_code: str = "USD") -> None:
        """Print net worth on a specific month.

        Args:
            month (Month): Month object
            currency (str): Currency code (default: "USD")

        Returns:
            None
        """
        with self._uow() as uow:
            nw = uow.net_worth.get(month, currency_code)
        if not nw:
            raise ValueError(f"No net worth data found for {month} in {currency_code}")
        print(
            f"Month: {month} Currency: {currency_code} Assets: {nw.assets:,} "
            f"Liabilities: {nw.liabilities:,} Net Worth: {nw.net_worth:,}"
        )

    def _get_balance_count_per_month(self) -> list[tuple[Month, int]]:
        """Get count of balance entries per month.

        Returns:
            list[tuple[Month, int]]: list of tuples Month count of balance entries.
        """
        with self._uow() as uow:
            counts = uow.balances.count_per_month()
        return counts

    def _get_month_balances(
        self, month: Month, active_only: bool = True
    ) -> list[Balance]:
        """Get balance all accounts on a specific month.

        Args:
            month (Month): Month object
            active_only (bool): Whether to include only active accounts

        Return:
            list[Balance]: List of Balance object for the specified account and month.
        """
        with self._uow() as uow:
            balances = uow.balances.get_month(month, active_only)
        return balances


def main() -> None:
    from nwtrack.compose import build_base_sqlite_uow_container

    container = build_base_sqlite_uow_container()
    container.register(
        RollBalancesUpdater,
        lambda c: RollBalancesUpdater(uow=lambda: c.resolve(UnitOfWork)),
    )
    updater: RollBalancesUpdater = container.resolve(RollBalancesUpdater)
    updater.run()


if __name__ == "__main__":
    main()
