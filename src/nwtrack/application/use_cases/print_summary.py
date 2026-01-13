"""
Print network summary by category
"""

import logging
from typing import Callable

from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.domain.models import Account, Balance, Category
from nwtrack.domain.value_objects import Month

logger = logging.getLogger(__name__)


class SummaryService:
    """Print net worth summary by category."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow

    def run(self) -> None:
        logger.info("Starting Print Summary Service")
        self.print_active_accounts()
        month = self.select_month()
        if month is None:
            logger.warning("No month selected. Exiting.")
            print("No month selected. Exiting.")
            return
        self.print_balances(month)
        self.print_summary_by_category(month)
        self.print_net_worth(month)
        logger.info("Finished Print Summary Service")

    def select_month(self, n_months: int = 5) -> Month | None:
        balance_counts = self._get_balance_count_per_month()
        balance_counts.sort(key=lambda x: x[0], reverse=True)
        recent_months = [month for month, _ in balance_counts[:n_months]]
        print("Select a month:")
        for idx, month in enumerate(recent_months):
            print(f"  {idx:2}. {month} ({balance_counts[idx][1]} entries)")
        print("   A. Enter year and month")
        print("   Q. Quit")
        while True:
            choice = input(f"Enter choice (0-{n_months - 1}, A, Q): ")
            if choice.lower().strip() == "q":
                return None
            if choice.lower().strip() == "a":
                return self.input_month()
            try:
                choice_idx = int(choice)
                if 0 <= choice_idx < n_months:
                    return recent_months[choice_idx]
                else:
                    print(f"Choice {choice_idx} out of range. Please try again.")
            except ValueError as e:
                print(f"Invalid input {e}.  Please try again.")

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
            with self._uow() as uow:
                if not uow.balances.check_month(month):
                    print(f"No balance entries found for {month}.")
                    continue
            break
        return month

    def print_active_accounts(self):
        active_accounts = self._get_active_accounts()
        print("Active accounts:")
        for account in active_accounts:
            _id, _name = account.id, account.name
            _category = self._get_category_by_account_id(_id)
            _side = _category.side.value
            print(f"  {_id:2}. {_name:20} {_category.name:18} {_side:10}")
        print()

    def print_balances(self, month: Month):
        balances = self._get_month_balances(month, active_only=True)
        account_map = self._get_map_id_to_account()
        print("Balances for", month)
        for balance in balances:
            account_id = balance.account_id
            account_name = account_map[account_id].name
            account_category = self._get_category_by_account_id(account_id)
            if account_category is None:
                logger.error("Category not found for account ID {%}", account_id)
                account_side = "Unknown"
            else:
                account_side = account_category.side.value
            print(
                f"  {account_id:2}. {account_name:20} {account_side:10} "
                f"{balance.amount:8,}"
            )
        print()

    def print_summary_by_category(self, month: Month) -> None:
        """Print summary by category for a specific month.
        Args:
            month (Month): Month object
        Returns:
            None
        """
        with self._uow() as uow:
            monthly_balances = uow._reporting.monthly_balance_total_by_category(month)
        print(f"Summary by category for {month}:")
        for mb in monthly_balances:
            category_name = mb.category.name
            category_side = mb.category.side.value
            amount = mb.amount
            print(f"  {category_name:16} {category_side:10} Total: {amount:8,}")
        print()

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
        print(f"Net Worth Summary for {month} ({currency_code}):")
        print(
            f"  Assets:      {nw.assets:9,}\n"
            f"  Liabilities: {nw.liabilities:9,}\n"
            f"  Net Worth:   {nw.net_worth:9,}"
        )

    def _get_category_by_account_id(self, account_id: int) -> Category | None:
        """Get category side for a given account ID.

        Args:
            account_id (int): Account ID

        Returns:
            Category | None: Category instance if found, else None.
        """
        with self._uow() as uow:
            account = uow.accounts.get_by_id(account_id)
        if not account:
            return None
        with self._uow() as uow:
            category = uow.categories.get(account.category_name)
        return category

    def _get_map_id_to_account(self) -> dict[int, Account]:
        """Get a map of account id to Account objects.

        Returns:
            dict[int, Account]: Map of account id to Account objects.
        """
        with self._uow() as uow:
            accounts = uow.accounts.get_all()
        return {acc.id: acc for acc in accounts}

    def _get_balance_count_per_month(self) -> list[tuple[Month, int]]:
        """Get count of balance entries per month.

        Returns:
            list[tuple[Month, int]]: list of tuples Month count of balance entries.
        """
        with self._uow() as uow:
            counts = uow.balances.count_per_month()
        return counts

    def _get_active_accounts(self) -> list[Account]:
        """Get list of active accounts.

        Returns:
            list[Account]: List of active Account objects.
        """
        with self._uow() as uow:
            accounts = uow.accounts.get_active()
        return accounts

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
    from dotenv import load_dotenv

    from nwtrack.bootstrap.composition import build_base_sqlite_uow_container
    from nwtrack.bootstrap.logging_config import setup_logging

    load_dotenv()
    setup_logging()

    container = build_base_sqlite_uow_container()
    container.register(
        SummaryService,
        lambda c: SummaryService(uow=lambda: c.resolve(UnitOfWork)),
    )
    service: SummaryService = container.resolve(SummaryService)
    service.run()


if __name__ == "__main__":
    main()
