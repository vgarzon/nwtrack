"""
Fetch service module for read-only data retrieval.
"""

from collections.abc import Callable

from nwtrack.application.dto import MonthlyCategoryBalance
from nwtrack.application.ports.uow import UnitOfWork
from nwtrack.domain.models import (
    Account,
    Balance,
    Category,
    Currency,
    Institution,
    NetWorth,
    Tag,
)
from nwtrack.domain.value_objects import Month


class FetchService:
    """Read-only data fetching service."""

    def __init__(self, uow: Callable[[], UnitOfWork]) -> None:
        self._uow = uow

    def get_accounts(self, active_only: bool = True) -> list[Account]:
        """Get a list of all accounts.

        Args:
            active_only (bool): Whether to include only active accounts.

        Returns:
            list[Account]: List of active Account objects.
        """
        if active_only:
            with self._uow() as uow:
                accounts = uow.accounts.get_active()
        else:
            with self._uow() as uow:
                accounts = uow.accounts.get_all()
        return accounts

    def get_all_categories(self) -> list[Category]:
        """Get a list of all categories.

        Returns:
            list[Category]: List of Category objects.
        """
        with self._uow() as uow:
            categories = uow.categories.get_all()
        return categories

    def get_all_currencies(self) -> list[Currency]:
        """Get a list of all currencies.

        Returns:
            list[Currency]: List of currency codes.
        """
        with self._uow() as uow:
            currencies = uow.currencies.get_all()
        return currencies

    def get_all_institutions(self) -> list[Institution]:
        """Get institutions for account workflow selection."""
        with self._uow() as uow:
            institutions = uow.institutions.get_all()
        return institutions

    def get_all_tags(self) -> list[Tag]:
        """Get tags for account workflow selection."""
        with self._uow() as uow:
            tags = uow.tags.get_all()
        return tags

    def get_account_by_id(self, account_id: int) -> Account | None:
        """Get account by ID.

        Args:
            account_id (int): Account ID

        Returns:
            Account | None: Account instance if found, else None.
        """
        with self._uow() as uow:
            account = uow.accounts.get_by_id(account_id)
        return account

    def get_balance_by_id(self, balance_id: int) -> Balance | None:
        """Get balance by ID.

        Args:
            balance_id (int): Balance ID

        Returns:
            Balance | None: Balance instance if found, else None.
        """
        with self._uow() as uow:
            balance = uow.balances.get_by_id(balance_id)
        return balance

    def get_balance_for_account_id(self, month: Month, account_id: int) -> Balance:
        """Get balance for an account on a specific month.

        Args:
            month (Month): Month object
            account_id (int): Account id

        Return:
            Balance: Balance object for the specified account and month.
        """
        with self._uow() as uow:
            balance = uow.balances.get_by_account_id(month, account_id)
        return balance

    def get_category_by_name(self, category_name: str) -> Category | None:
        """Get category by name.

        Args:
            category_name (str): Category name

        Returns:
            Category | None: Category instance if found, else None.
        """
        with self._uow() as uow:
            category = uow.categories.get(category_name)
        return category

    def get_networth(self, month: Month, currency_code: str = "USD") -> NetWorth | None:
        """Get net worth for a specific month and currency.

        Args:
            month (Month): Month object
            currency_code (str, optional): The currency code. Defaults to "USD".

        Returns:
            Networth | None: Net worth amount if found, else None.
        """
        with self._uow() as uow:
            networth = uow.net_worth.get(month, currency_code)
        return networth

    def get_last_n_networth(self, n: int, currency_code: str = "USD") -> list:
        """Get last n months of net worth history for a given currency.

        Args:
            n (int): Number of months to retrieve.
            currency_code (str, optional): The currency code. Defaults to "USD".

        Returns:
            list: List of Net Worth records.
        """
        with self._uow() as uow:
            last_n = uow.net_worth.get_last_n(n, currency_code)
        return last_n

    def get_balance_count_per_month(self) -> list[tuple[Month, int]]:
        """Get count of balance entries per month.

        Returns:
            list[tuple[Month, int]]: list of tuples Month count of balance entries.
        """
        # TODO: specify number of months to retrieve
        with self._uow() as uow:
            counts = uow.balances.count_per_month()
        return counts

    def get_recent_months(self, n_months=12) -> list[Month]:
        """Get sorted list of recent months with balances.

        Args:
            n_months (int): Number of recent months to retrieve, default is 12

        Returns:
            list[Month]: List of recent months in descending order.
        """
        balance_counts = self.get_balance_count_per_month()
        if not balance_counts:
            return []
        balance_counts.sort(key=lambda x: x[0], reverse=True)
        recent_months = [month for month, _ in balance_counts[:n_months]]
        return recent_months

    def get_month_balances(
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

    def check_month_in_balances(self, month: Month) -> bool:
        """Check if there are balance entries for a specific month.
        Args:
            month (Month): Month object
                Returns:
            bool: True if entries exist, False if not
        """
        with self._uow() as uow:
            result = uow.balances.check_month(month)
        return result

    def get_balance_count_for_month(self, source_month: Month) -> int:
        """Get count of balance entries for a specific month.
        Args:
            source_month (Month): Month object
        Returns:
            int: Count of balance entries for the month.
        """
        with self._uow() as uow:
            count = uow.balances.count_for_month(source_month)
        return count

    def get_monthly_balance_total_by_category(
        self, month: Month
    ) -> list[MonthlyCategoryBalance]:
        """Get total balance per category for a specific month.
        Args:
            month (Month): Month object
        Returns:
           list[MonthlyCategoryBalance]: List of MonthlyCategoryBalance objects.
        """
        with self._uow() as uow:
            monthly_balances = uow._reporting.monthly_balance_total_by_category(month)
        return monthly_balances
